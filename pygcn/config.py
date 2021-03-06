import numpy as np
n_hidden_low = 5
n_hidden_high = 100
dropout_low = 0.0
dropout_high = 1.0
lr_low = -5
lr_high = 0
weight_decay_low = -5
weight_decay_high = 0
epochs_low = 20
epochs_high = 250
seed = 28
early_stop = 20
min_epoch = 50
alpha = 0.1
epsilon = 0.001
#sample
sample_epochs = 200
sample_nhidden = 16
sample_dropout = 0.5
sample_lr = np.log10(0.01)
sample_weight_decay = -4 +  np.log10(5)
#ga
countTime = 0
time_out = 0.5
simulations = 1
generations = 10
size = 15
mutation_rate = 0.1
fitness_cutoff = 0.5
#pso
n_iterations = 10
n_particles = 15
#abc
colony_size = 14