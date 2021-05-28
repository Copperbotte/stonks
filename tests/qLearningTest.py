import matplotlib.pyplot as plt
import numpy as np
import random

#uses a neural net style matrix to find a shortest path through a weighted graph
def rndarr(c=2, r=2):
    m = np.empty((r, c))
    for C in range(c):
        for R in range(r):
            m[R][C] = random.random()
    return m

#inits a list of matrices, from a list of node lengths.
def initMatrices(shape):
    return [rndarr(s,e) for s,e in zip(shape[:-1], shape[1:])]

#prints the matrices
def printMatrices(arrs):
    for a in arrs:
        print(a, '\n')



#does a bunch of operations:
#checks if the state is in the qtable. If not, initializes it to zero.
#State is a tuple, with the current layer and node number. (layer, node)
#Choose a next state randomly.
#   (replace later with a baysean estimate or a max func)
#If the state isn't the final state, recursively call q_step
#   q_step returns the the discounted cost
#If the state is the final state, return 0.

#init a state if not in the qtable, otherwise return state data.
def q_get(qtable, state):
    if state not in qtable.keys():
        qtable[state] = 0
    return qtable[state]

#update q table for this current state
def q_step(qtable, shape, arrs, state, discount=0.5):
    #if the state is the final state, no q-value.
    if state[0] == len(shape) - 1:
        return 0
    
    #get the q-values of the future states
    len_next = shape[state[0]+1]
    q_value = [q_get(qtable, (state[0]+1, i)) for i in range(len_next)]

    #get the reward for approaching those future states
    #current state -> future state + discounted q-value
    selector = [1 if n == state[1] else 0 for n in range(shape[state[0]])]
    rewards = arrs[state[0]] @ np.array([selector]).transpose()

    #find the q-values at this step using the bellman equation
    q_set = rewards + discount * np.array([q_value]).transpose()
    #q_max = np.max(q_set)

    #set the state in the qtable for this path
    #q_set(qtable, state, q_max)
    #qtable[state] = q_max
    return q_set

#step through the weighted graph using a path trace
#update q-table by tracing the graph backwards
def q_update_montecarlo(qtable, shape, arrs, discount=0.5):
    #choose a random path
    path = [random.randrange(0, i) for i in shape]

    #update q table from the back to the front
    for state in reversed(list(enumerate(path))):
        q_set = q_step(qtable, shape, arrs, state, discount=discount**state[0])
        qtable[state] = np.max(q_set)

def q_traverse_max(qtable, shape, arrs):
    state = (0, 0)
    print(state)
    for e in list(enumerate(shape))[1:]:
        #get q values and rewards
        q_set = q_step(qtable, shape, arrs, state)

        #get the index of the path with the max reward
        q_set = q_set.transpose()[0]
        q_index = np.argmax(q_set)
        q_max = q_set[q_index]

        #set new state
        state = (state[0] + 1, q_index)
        print(state, q_max)
    

if __name__ == "__main__":
    global shape
    global arrs
    global qtable

    random.seed(3141592) #common seed for deterministic results

    #shape = [1,2,3,1]
    shape = [1,400,400,400,1]
    arrs = initMatrices(shape)
    #printMatrices(arrs) #dont print the 400 matrix one

    qtable = dict()

    for i in range(1000):
        q_update_montecarlo(qtable, shape, arrs)

    q_traverse_max(qtable, shape, arrs)
