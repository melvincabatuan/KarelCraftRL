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


class CliffEnv:

    def __init__(self, render=True) -> None:
        '''
        CliffEnv constructor
        '''
        self.cols, self.rows = world_size()
        self.num_states = self.cols * self.rows
        self.actions = ['up', 'right', 'down', 'left']  # action space
        self.q_values = np.zeros((self.num_states, len(self.actions)))
        self.agent_position = (3, 0)  # bottom-left
        self.render = render
        self.set_rewards()
        self.set_model_path()

    def set_rewards(self):
        self.rewards = np.full((self.rows, self.cols), -1.)
        for col_idx in range(1, self.cols):
            self.rewards[self.rows - 1, col_idx] = -100.
        self.rewards[-1, -1] = 100.

    def set_model_path(self) -> None:
        self.model_dir = os.path.join('training', 'model')
        pathlib.Path(self.model_dir).mkdir(parents=True, exist_ok=True)

    def vec2id(self, position):
        '''
        Maps 2d numpy position into 1d or id
        '''
        return position[0] * self.cols + position[1]

    def step(self, action_idx):
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
        return self.vec2id(observation), reward, done

    def is_terminal_state(self, point) -> bool:
        '''
        Determines if the specified location is a terminal state
        '''
        return self.rewards[point[0], point[1]] != -1.

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

    def egreedy_policy(self, state, epsilon=0.1):
        '''
        Choose an action based on a epsilon greedy policy.
        A random action is selected with epsilon probability, else select the best action.
        '''
        if np.random.random() < epsilon:
            return np.random.choice(len(self.actions))
        else:
            return np.argmax(self.q_values[state])

    def learn(self, mode='sarsa', num_episodes=1000, epsilon=0.9, discount_factor=0.8, learning_rate=0.2, exploration_rate=0.1):
        # Training Sarsa
        for i in range(num_episodes):
            prompt(f'Train episode: {i}')
            self.agent_position = (3, 0)  # bottom-left
            if self.render:
                world_start_pt = reset()
                self.agent_position = self.world2numpy(world_start_pt, self.rows)
            observation = self.agent_position
            state = self.vec2id(observation)

            if mode == 'sarsa':  # get next action
                action = self.egreedy_policy(state, exploration_rate)

            done = False
            while not done:

                if mode != 'sarsa':
                    action = self.egreedy_policy(state, exploration_rate)

                next_state, reward, done = self.step(action)

                if mode == 'sarsa':
                    # Choose next action
                    next_action = self.egreedy_policy(next_state, exploration_rate)

                    # Update q_values
                    td_target = reward + discount_factor * self.q_values[next_state][next_action]
                    td_error = td_target - self.q_values[state][action]

                    self.q_values[state][action] += learning_rate * td_error  # new q value

                    # Update state
                    state = next_state
                    action = next_action

                else:  # q-learning
                    td_target = reward + discount_factor * np.max(self.q_values[next_state])
                    td_error = td_target - self.q_values[state][action]
                    self.q_values[state][action] += learning_rate * td_error
                    # Update state
                    state = next_state

        print(self.q_values)
        np.save(self.model_dir + '/cliff_q_values.npy', self.q_values)
        prompt('Training complete!')

    def play(self, num_episodes=10):
        self.render = True
        self.q_values = np.load(self.model_dir + '/cliff_q_values.npy')
        print('Successfully loaded model ...')
        for i in range(10):
            prompt(f'Play Episode: {i}')
            world_start_pt = reset()
            numpy_pt = self.world2numpy(world_start_pt, self.rows)
            state = self.vec2id(numpy_pt)

            done = False
            while not done:
                action = self.egreedy_policy(state, 0.0)
                next_state, reward, done = self.step(action)

                # Update state and action
                state = next_state
        prompt('Play test complete!')


def main():
    env = CliffEnv(render=False)
    if MODE == 'learn':
        env.learn('qlearn')
        # env.learn('sarsa')
    elif MODE == 'play':
        env.play()  # needs q_values stored in ./training/model/ dir
    else:
        print('WARN: Unknown mode.. proceed with learning...')
        env.learn()


if __name__ == "__main__":
    run_karel_program('12x4')
