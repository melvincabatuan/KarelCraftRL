from karelcraft.karelcraft import *
import os
import pathlib
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


class LavaEnv:

    def __init__(self, render=True) -> None:
        '''
        LavaEnv constructor
        '''
        self.cols, self.rows = world_size()
        self.actions = ['up', 'right', 'down', 'left']  # action space
        self.q_values = np.zeros((self.rows, self.cols, len(self.actions)))
        self.render = render
        self.set_rewards()
        self.set_model_path()

    def set_rewards(self) -> None:
        self.rewards = np.full((self.rows, self.cols), -100.)
        self.rewards[0, 5] = 100.  # goal
        hallway = {}
        hallway[1] = [i for i in range(1, 10)]
        hallway[2] = [1, 3, 7]
        hallway[3] = [i for i in range(3, 10)]
        hallway[3].append(1)
        hallway[4] = [3, 7]
        hallway[5] = [i for i in range(11)]
        hallway[6] = [6]
        hallway[7] = [i for i in range(1, 10)]
        hallway[8] = [3, 7]
        hallway[9] = [i for i in range(11)]
        # Set hallway rewards
        for row_idx in range(1, 10):
            for col_idx in hallway[row_idx]:
                self.rewards[row_idx, col_idx] = -1.

    def set_model_path(self) -> None:
        self.model_dir = os.path.join('training', 'model')
        pathlib.Path(self.model_dir).mkdir(parents=True, exist_ok=True)

    def step(self, action_idx) -> tuple:
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

        self.agent_position = observation  # update agent position
        reward = self.rewards[observation[0], observation[1]]
        done = self.is_terminal_state(observation)
        return observation, reward, done

    @staticmethod
    def numpy2world(point, num_rows) -> tuple:
        '''
        Converts numpy convention (0, 0) at top left
        to world convention (0, 0) at bottom left
        '''
        return (point[1], num_rows - 1 - point[0])

    @staticmethod
    def world2numpy(point, num_rows) -> tuple:
        '''
        Converts world convention (0, 0) at bottom left
        to numpy convention (0, 0) at top left
        '''
        return (num_rows - 1 - point[1], point[0])

    def is_terminal_state(self, point) -> bool:
        '''
        Determines if the specified location is a terminal state
        '''
        return self.rewards[point[0], point[1]] != -1.

    def get_start_location(self) -> tuple:
        '''
        Choose a random, non-terminal starting location
        '''
        row_idx = np.random.randint(self.rows)
        col_idx = np.random.randint(self.cols)
        while self.is_terminal_state((row_idx, col_idx)):
            row_idx = np.random.randint(self.rows)
            col_idx = np.random.randint(self.cols)
        return (row_idx, col_idx)

    def get_next_action(self, point, epsilon) -> int:
        '''
        epsilon greedy algorithm that will choose which action to take next
        '''
        if np.random.random() < epsilon:
            return np.argmax(self.q_values[point[0], point[1]])
        else:
            return np.random.randint(len(self.actions))  # choose a random action

    def get_shortest_path(self, start_point) -> list:
        shortest_path = []
        if self.is_terminal_state(start_point):
            return shortest_path
        else:
            current_state = start_point
            shortest_path.append(self.numpy2world(start_point, self.rows))
            done = False
            while not done:
                action_idx = self.get_next_action(current_state, 1.)
                current_state, _, done = self.step(action_idx)
                shortest_path.append(self.numpy2world(current_state, self.rows))
        return shortest_path

    def learn(self, num_episodes=1000, epsilon=0.9, discount_factor=0.9, learning_rate=0.9) -> None:
        '''
        epsilon - percent of time to take the best action (instead of a random)
        discount_factor  - discount factor for future rewards
        learning_rate - the rate at which the AI agent should learn
        '''
        for i in range(num_episodes):
            prompt(f'Train episode: {i}')
            self.agent_position = self.get_start_location()
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
                temporal_difference = reward + \
                    (discount_factor *
                     np.max(self.q_values[observation[0], observation[1]])) - old_q_value

                # update the Q-value for the previous state and action pair
                new_q_value = old_q_value + (learning_rate * temporal_difference)  # Bellman
                self.q_values[old_state[0], old_state[1], action_idx] = new_q_value

        print(self.q_values)
        np.save(self.model_dir + '/lava_q_values.npy', self.q_values)
        prompt('Training complete!')

    def play(self, num_episodes=10) -> None:
        self.render = True
        self.q_values = np.load(self.model_dir + '/lava_q_values.npy')
        print('Successfully loaded model ...')
        for i in range(num_episodes):
            random_point = self.get_start_location()
            start_point = self.numpy2world(random_point, self.rows)
            reset(start_point)
            observation = random_point
            prompt(f'Play Episode: {i}')
            done = False
            action_list = []
            while not done:
                paint_corner('azure')  # path
                action_idx = self.get_next_action(observation, 1.)
                observation, _, done = self.step(action_idx)
                action_list.append(action_idx)

            pick_beeper()  # Pick package
            self.back_track(action_list)  # Back to start
            put_beeper()  # Deliver package
            prompt('Play test complete!')

    def back_track(self, action_list) -> None:
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
    env = LavaEnv(render=False)
    if MODE == 'learn':
        env.learn()
    elif MODE == 'play':
        env.play()  # needs q_values stored in ./training/model/ dir
    else:
        print('WARN: Unknown mode.. proceed with learning...')
        env.learn()


if __name__ == '__main__':
    run_karel_program('11x11v2')
