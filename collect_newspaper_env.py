'''
@author: MKC
Simple Q-learning with KarelCraft
'''


from karelcraft.karelcraft import *
import os
from pathlib import Path
import numpy as np

# MODE = 'learn'
MODE = 'play'

# Karel Actions


def safe_move():
    if front_is_clear():
        move()


def move_up():
    while not_facing_north():
        turn_left()
    safe_move()


def move_right():
    while not_facing_east():
        turn_left()
    safe_move()


def move_down():
    while not_facing_south():
        turn_left()
    safe_move()


def move_left():
    while not_facing_west():
        turn_left()
    safe_move()


def turn_around():
    turn_left()
    turn_left()


class CollectNewspaperEnv:

    def __init__(self, render=True) -> None:
        '''
        CollectNewspaperEnv constructor
        '''
        self.cols, self.rows = world_size()
        self.actions = ['up', 'right', 'down', 'left']  # action space
        self.q_values = np.zeros((self.rows, self.cols, len(self.actions)))
        self.agent_position = (1, 2)
        self.render = render
        self.set_rewards()
        self.set_model_path()

    def set_rewards(self) -> None:
        self.rewards = np.full((self.rows, self.cols), -100.)
        self.rewards[2, 5] = 100.  # goal
        self.rewards[1:4, 2:5] = -1.
        print(self.rewards)

    def set_model_path(self):
        self.model_dir = os.path.join('training', 'model')
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, Path(__file__).stem + '_q_values.npy')

    def step(self, action_idx):
        '''
        Perform the action in the environment
        '''
        action = self.actions[action_idx]
        if self.render:
            if action == 'up':
                move_up()
            elif action == 'right':
                move_right()
            elif action == 'down':
                move_down()
            elif action == 'left':
                move_left()
            else:  # no action
                print("No action.")

            world_position = get_position()
            observation = self.world2numpy(world_position, self.rows)

        else:
            new_row_idx = self.agent_position[0]
            new_col_idx = self.agent_position[1]

            if action == 'up' and new_row_idx > 0:
                new_row_idx -= 1
            elif action == 'right' and new_col_idx < self.cols - 1:
                new_col_idx += 1
            elif action == 'down' and new_row_idx < self.rows - 1:
                new_row_idx += 1
            elif action == 'left' and new_col_idx > 0:
                new_col_idx -= 1

            observation = (new_row_idx, new_col_idx)

        # update position with current observation (used by no render mode)
        self.agent_position = observation
        reward = self.rewards[observation[0], observation[1]]
        done = self.is_terminal_state(observation)
        return observation, reward, done

    @staticmethod
    def numpy2world(point, num_rows):
        '''
        Converts numpy convention (0, 0) at top left
        to world convention (0, 0) at bottom left
        '''
        return (point[1], num_rows - 1 - point[0])

    @staticmethod
    def world2numpy(point, num_rows):
        '''
        Converts world convention (0, 0) at bottom left
        to numpy convention (0, 0) at top left
        '''
        return (num_rows - 1 - point[1], point[0])

    def is_terminal_state(self, point):
        '''
        Determines if the specified location is a terminal state
        '''
        return self.rewards[point[0], point[1]] != -1.

    def get_next_action(self, point, epsilon):
        '''
        epsilon greedy algorithm that will choose which action to take next
        '''
        if np.random.random() < epsilon:
            return np.argmax(self.q_values[point[0], point[1]])
        else:
            return np.random.randint(4)  # choose a random action

    def learn(self, num_episodes=500, epsilon=0.9, discount_factor=0.9, learning_rate=0.9):
        '''
        epsilon - percent of time to take the best action (instead of a random)
        discount_factor  - discount factor for future rewards
        learning_rate - the rate at which the AI agent should learn
        '''
        for i in range(num_episodes):
            prompt(f'Train episode: {i}')
            self.agent_position = (1, 2)
            observation = self.agent_position
            if self.render:
                start_point = self.numpy2world(self.agent_position, self.rows)
                reset(start_point)

            done = False
            while not done:
                action_idx = self.get_next_action(observation, epsilon)
                old_state = observation
                observation, reward, done = self.step(action_idx)

                # update q values
                old_q_value = self.q_values[old_state[0], old_state[1], action_idx]
                temporal_diff = reward + \
                    (discount_factor *
                     np.max(self.q_values[observation[0], observation[1]])) - old_q_value

                # update the Q-value for the previous state and action pair
                new_q_value = old_q_value + (learning_rate * temporal_diff)  # Bellman
                self.q_values[old_state[0], old_state[1], action_idx] = new_q_value

        print(self.q_values)

        # self.model_path = self.model_dir + '/' + Path(__file__).stem + '_q_values.npy'
        # self.model_path = os.path.join(self.model_dir, Path(__file__).stem + '_q_values.npy')
        np.save(self.model_path, self.q_values)
        prompt('Training complete!')

    def play(self, num_episodes=10):
        self.render = True
        self.q_values = np.load(self.model_path)
        print('Successfully loaded model ...')
        for i in range(num_episodes):
            numpy_start = (1, 2)
            start_point = self.numpy2world(numpy_start, self.rows)
            reset(start_point)
            observation = numpy_start
            prompt(f'Play Episode: {i}')
            done = False
            action_list = []
            while not done:
                paint_corner('red')  # path
                action_idx = self.get_next_action(observation, 1.)
                observation, _, done = self.step(action_idx)
                action_list.append(action_idx)

            # Pick package
            pick_beeper()

            # Go back to start
            self.back_track(action_list)
            turn_around()
            if color_present():
                remove_paint()
            prompt('\t Play test complete!')

    def back_track(self, action_list):
        for i in reversed(action_list):
            if color_present():
                remove_paint()
            action = self.actions[i]
            if action == 'up':
                move_down()
            elif action == 'right':
                move_left()
            elif action == 'down':
                move_up()
            elif action == 'left':
                move_right()
            else:  # no action
                print("No action.")


def main():
    env = CollectNewspaperEnv(render=False)
    if MODE == 'learn':
        env.learn()
    elif MODE == 'play':
        env.play()  # needs q_values stored in ./training/model/ dir
    else:
        print('WARN: Unknown mode.. proceed with learning...')
        env.learn()


if __name__ == '__main__':
    run_karel_program('collect_newspaper_karel')
