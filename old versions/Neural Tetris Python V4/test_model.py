import torch
from tetris import Tetris

SAVED_PATH = "trained_models"


def test():
    if torch.cuda.is_available():
        torch.cuda.manual_seed(123)
    else:
        torch.manual_seed(123)
    if torch.cuda.is_available():
        model = torch.load("{}/tetris".format(SAVED_PATH))
    else:
        model = torch.load("{}/tetris".format(SAVED_PATH), map_location=lambda storage, loc: storage)
    model.eval()
    env = Tetris()
    env.reset()
    if torch.cuda.is_available():
        model.cuda()
    while True:
        next_steps = env.get_next_states()
        next_actions, next_states = zip(*next_steps.items())
        next_states = torch.stack(next_states)
        if torch.cuda.is_available():
            next_states = next_states.cuda()
        predictions = model(next_states)[:, 0]
        index = torch.argmax(predictions).item()
        action = next_actions[index]
        reward, done = env.step(action, render=True)

        if done:
            print("Cleared lines: " + str(reward))
            break


if __name__ == "__main__":
    test()
