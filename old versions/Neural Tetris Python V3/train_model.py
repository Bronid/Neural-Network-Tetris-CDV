from random import random, randint, sample

import numpy as np
import torch
import torch.nn as nn

from NN import DQN
from tetris import Tetris
from collections import deque


SAVED_PATH = "trained_models"
REPLAY_MEMORY_SIZE = 30000
SAVE_INTERVAL = 500
NUM_DECAY_EPOCHS = 2000
NUM_EPOCHS = 5000
INITEPSILON = 1
FINALEPSILON = 1e-3
LR = 1e-3
BATCH_SIZE = 512
GAMMA = 0.999
RENDER = True


def train():
    if torch.cuda.is_available():
        torch.cuda.manual_seed(123)
    else:
        torch.manual_seed(123)
    env = Tetris()
    model = DQN()
    optimizer = torch.optim.Adam(model.parameters(), LR)
    criterion = nn.MSELoss()

    state = env.reset()
    if torch.cuda.is_available():
        model.cuda()
        state = state.cuda()

    replay_memory = deque(maxlen=REPLAY_MEMORY_SIZE)
    epoch = 0
    while epoch < NUM_EPOCHS:
        next_steps = env.get_next_states()
        # Exploration or exploitation
        epsilon = FINALEPSILON + (max(NUM_DECAY_EPOCHS - epoch, 0) * (
                INITEPSILON - FINALEPSILON) / NUM_DECAY_EPOCHS)
        u = random()
        random_action = u <= epsilon
        next_actions, next_states = zip(*next_steps.items())
        next_states = torch.stack(next_states)
        if torch.cuda.is_available():
            next_states = next_states.cuda()
        model.eval()
        with torch.no_grad():
            predictions = model(next_states)[:, 0]
        model.train()
        if random_action:
            index = randint(0, len(next_steps) - 1)
        else:
            index = torch.argmax(predictions).item()

        next_state = next_states[index, :]
        action = next_actions[index]

        reward, done = env.step(action, render=RENDER)

        if torch.cuda.is_available():
            next_state = next_state.cuda()
        replay_memory.append([state, reward, next_state, done])
        if done:
            state = env.reset()
            if torch.cuda.is_available():
                state = state.cuda()
        else:
            state = next_state
            continue
        if len(replay_memory) < REPLAY_MEMORY_SIZE / 10:
            continue
        epoch += 1
        batch = sample(replay_memory, min(len(replay_memory), BATCH_SIZE))
        state_batch, reward_batch, next_state_batch, done_batch = zip(*batch)
        state_batch = torch.stack(tuple(state for state in state_batch))
        reward_batch = torch.from_numpy(np.array(reward_batch, dtype=np.float32)[:, None])
        next_state_batch = torch.stack(tuple(state for state in next_state_batch))

        if torch.cuda.is_available():
            state_batch = state_batch.cuda()
            reward_batch = reward_batch.cuda()
            next_state_batch = next_state_batch.cuda()

        q_values = model(state_batch)
        model.eval()
        with torch.no_grad():
            next_prediction_batch = model(next_state_batch)
        model.train()

        y_batch = torch.cat(
            tuple(reward if done else reward + GAMMA * prediction for reward, done, prediction in
                  zip(reward_batch, done_batch, next_prediction_batch)))[:, None]

        optimizer.zero_grad()
        loss = criterion(q_values, y_batch)
        loss.backward()
        optimizer.step()

        print("Epoch: " + str(epoch) + "/" + str(NUM_EPOCHS))
        print("Action: " + str(action))
        print("Cleared lines: " + str(reward))

        if epoch > 0 and epoch % SAVE_INTERVAL == 0:
            torch.save(model, "{}/tetris_{}".format(SAVED_PATH, epoch))

    torch.save(model, "{}/tetris".format(SAVED_PATH))


if __name__ == "__main__":
    train()
