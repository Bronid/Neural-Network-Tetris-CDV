import math
import random
import sys
from itertools import count

import torch
import torch.nn as nn
import torch.optim as optim
from PyQt5.QtWidgets import QApplication

from main import Tetris
from model import DQN
from replay_memory import ReplayMemory, Transition

# if gpu is to be used
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BATCH_SIZE = 128
GAMMA = 0.999
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 200
TARGET_UPDATE = 10

n_actions = 0

policy_net = DQN().to(device)
target_net = DQN().to(device)
target_net.load_state_dict(policy_net.state_dict())
target_net.eval()

optimizer = optim.Adam(policy_net.parameters())
memory = ReplayMemory(10000)

steps_done = 0


def next_data(steps):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1

    next_actions, next_states = zip(*steps.items())
    next_states = torch.stack(next_states)
    if sample > eps_threshold:
        with torch.no_grad():
            ans = policy_net(next_states)[:, 0]
            index = torch.argmax(ans).item()
    else:
        index = random.randint(0, len(next_states)-1)

    return next_actions[index], next_states[index, :]


def optimize_model():
    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    batch = Transition(*zip(*transitions))  # Transpose the batch

    # Compute a mask of non-final states and concatenate the batch elements
    # (a final state would've been the one after which simulation ended)
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                            batch.next_state)), device=device, dtype=torch.bool)
    non_final_next_states = torch.cat([s for s in batch.next_state
                                       if s is not None])
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    state_action_values = policy_net(state_batch).gather(1, action_batch)

    # Compute V(s_{t+1}) for all next states.
    # Expected values of actions for non_final_next_states are computed based
    # on the "older" target_net; selecting their best reward with max(1)[0].
    # This is merged based on the mask, such that we'll have either the expected
    # state value or 0 in case the state was final.
    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0].detach()
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    # Compute Huber loss
    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    for param in policy_net.parameters():
        param.grad.data.clamp_(-1, 1)
    optimizer.step()


num_episodes = 50


def train(env):
    for i_episode in range(num_episodes):
        epoch(env)
        # Update the target network, copying all weights and biases in DQN
        if i_episode % TARGET_UPDATE == 0:
            target_net.load_state_dict(policy_net.state_dict())

    torch.save(policy_net.state_dict(), 'cringe.pt')
    print('Complete')


def epoch(env):
    # Initialize the environment and state
    state = env.tboard.reset()

    for _ in count():
        next_steps = env.tboard.get_next_states()
        print(env.tboard.cur_piece.pieceShape, env.tboard.cur_piece.num_rotations)
        print(next_steps)
        # Select and perform an action, observe new state
        action, next_state = next_data(next_steps)
        reward, done = env.tboard.step(action)
        reward = torch.tensor([reward], device=device)

        # Store the transition in memory
        memory.push(state, action, next_state, reward)

        # Perform one step of the optimization (on the policy network)
        # optimize_model()

        if not done:
            # Move to the next state
            state = next_state
        else:
            break


if __name__ == '__main__':
    app = QApplication([])
    environment = Tetris()
    epoch(environment)
    sys.exit(app.exec_())
