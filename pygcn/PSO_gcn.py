import random
import math
import time
from train import NetworkInstance
from utils import load_data, accuracy
from pygcn.models import GCN
import torch.nn.functional as F
import torch.optim as optim
from numpy.random import choice
import matplotlib.pyplot as plt
import numpy as np
import config as cf
import torch
global nfeat
global nclass
W = 0.5
c1 = 0.8
c2 = 0.9
n_iterations = cf.n_iterations
n_particles = cf.n_particles
early_stop = cf.early_stop
min_epoch = cf.min_epoch
simulations = 1
class Particle():
    def __init__(self):
        self.position = pso_generate_individual()
        self.pbest_position = self.position
        self.pbest_value = float('-inf')
        self.velocity = pso_initial_velocity()
    # def __str__(self):
    #     print("I am at", self.position, " my pbest is ", self.pbest_position)
    def move(self):
        self.position = winsorize(add(self.position, self.velocity))
    def get_fitness(self):
        net = NetworkInstance(**self.position)
        self.fitness, _ = train(net)
        #self.position["acc_val"] = self.fitness
        return self.fitness
    def __str__(self):
        return "Position: epochs: {:.2f}, n_hidden: {:.2f}, dropout: {:.3f}, lr: {:.4f}, weight_decay: {:.5f}, acc: {:.3f}".format(self.position["epochs"], self.position["n_hidden"], self.position["dropout"], self.position["lr"], self.position["weight_decay"], self.fitness)

class Space():
    def __init__(self, target, n_particles):
        self.target = target
        #self.target_error = target_error
        self.n_particles = n_particles
        self.particles = []
        self.gbest_value = float('-inf')
        self.gbest_position = pso_generate_individual()
    def print_particles(self):
        for particle in self.particles:
            #particle.__str__()
            print(particle)
    def fitness(self, particle):
        return 1 #particle.position[0] ** 2 + particle.position[1] ** 2 + 1
    def set_pbest(self):
        for particle in self.particles:
            particle.get_fitness()
            fitness_candidate = particle.fitness
            if (particle.pbest_value < fitness_candidate):
                particle.pbest_value = fitness_candidate
                particle.pbest_position = particle.position
    def set_gbest(self):
        for particle in self.particles:
            best_fitness_candidate = particle.fitness
            if (self.gbest_value < best_fitness_candidate):
                self.gbest_value = best_fitness_candidate
                self.gbest_position = particle.position
    def move_particles(self):
        for particle in self.particles:
            global W
            new_velocity = add(add(scale(W, particle.velocity), scale(c1 * random.random(), subtract(particle.pbest_position, particle.position))), scale(c2 * random.random(),  subtract(self.gbest_position, particle.position)))
            particle.velocity = new_velocity
            particle.move()
    def sort_particles_by_fitness(self):
        self.particles = sorted_by_fitness_population(self.particles)

def set_params_range(params_range):
    '''Set params range for all kinds of hyperparameters in the network'''
    params_range["n_hidden"]["lower"] = 5
    params_range["n_hidden"]["upper"] = 50
    params_range["dropout"]["lower"] = 0.1
    params_range["dropout"]["upper"] = 0.8
    params_range["learning_rate"]["lower"] = -6 #this param is searched on log scale
    params_range["learning_rate"]["upper"] = 1
    lower_x, upper_x = x_boundaries
    lower_y, upper_y = y_boundaries
    population = []
    # for i in range(size):
    #     individual = {
    #         "x": random.uniform(lower_x, upper_x),
    #         "y": random.uniform(lower_y, upper_y)
    #     } 
    #     population.append(individual)
    return population
def pso_generate_individual():
    global nfeat
    global nclass
    x = {}
    x = {"seed": cf.seed,
        "nfeat": nfeat,
        "nclass": nclass,
        "epochs": random.randint(cf.epochs_low, cf.epochs_high),
        "n_hidden": random.randint(cf.n_hidden_low, cf.n_hidden_high),
        "dropout": random.uniform(cf.dropout_low, cf.dropout_high),
        "lr": random.uniform(cf.lr_low, cf.lr_high),
        "weight_decay": random.uniform(cf.weight_decay_low, cf.weight_decay_high)
        }
    return x
def pso_initial_velocity():
    x = {}
    x = {"seed": 0,
        "nfeat": 0,
        "nclass": 0,
        "epochs": 0,
        "n_hidden": 0,
        "dropout": 0,
        "lr": 0,
        "weight_decay": 0
        }
    return x
def scale(a, indi):
    '''Scale all individual elements by scalar a'''
    indi["n_hidden"] = int(a * indi["n_hidden"]) #Todo: make sure value after scale stay in MaxMin range
    indi["dropout"] = a * indi["dropout"]
    indi["lr"] *= a
    indi["weight_decay"] *= a
    return indi

def winsorize(indi):
    indi["n_hidden"] = int(min(cf.n_hidden_high, max(indi["n_hidden"], cf.n_hidden_low)))
    indi["dropout"] = min(cf.dropout_high, max(indi["dropout"], cf.dropout_low))
    indi["epochs"] = int(min(cf.epochs_high, max(indi["epochs"], cf.epochs_low)))
    return indi
def subtract(a, b):
    c = a.copy()
    for key in a:
        c[key] = a[key] - b[key]
    return c
def add(a, b):
    c = a.copy()
    for key in a:
        c[key] = a[key] + b[key]
    return c
def a_random(param):
    if param == "n_hidden":
        return random.randint(cf.n_hidden_low, cf.n_hidden_high)
    elif param == "dropout":
        return random.uniform(cf.dropout_low, cf.dropout_high)
    elif param == "lr":
        return random.uniform(cf.lr_low, cf.lr_high)
    elif param == "weight_decay":
        return random.uniform(cf.weight_decay_low, cf.weight_decay_high)
    elif param == "epochs":
        return random.uniform(cf.epochs_low, cf.epochs_high)

def train(network):
    t_total = time.time()
    #network.make_model()
    model = network.model
    optimizer = network.optimizer
    losses_val = []
    #train
    epochs = network.params["epochs"]  
    torch.cuda.manual_seed(network.params["seed"])
    torch.manual_seed(network.params["seed"])
    np.random.seed(network.params["seed"])
    iter_since_best = 0
    best_loss_val = 10**9
    #min_epoch_ = min(min_epoch, epochs)
    for i in range(epochs):
        t = time.time()
        model.train()
        optimizer.zero_grad()
        output = model(features, adj)
        loss_train = F.nll_loss(output[idx_train], labels[idx_train])
        acc_train = accuracy(output[idx_train], labels[idx_train])
        loss_train.backward()
        optimizer.step()

        model.eval()
        output = model(features, adj)
        loss_val = F.nll_loss(output[idx_val], labels[idx_val])
        if (loss_val.item() < best_loss_val):
            iter_since_best = 0
            best_loss_val = loss_val.item()
        else:
            iter_since_best += 1
        losses_val.append(loss_val.item())
        acc_val = accuracy(output[idx_val], labels[idx_val])
        if i > min_epoch and iter_since_best > early_stop:
            print("Early stopping at...", i, " over ", epochs)
            break
    #print('Time: ', time.time() - t_total)
    return acc_val.item(), time.time() - t_total
    # print("Optimization Finished!")
    # print("Total time elapsed: {:.4f}s".format(time.time() - t_total))
def sorted_by_fitness_population(population):
    return sorted(population, key = lambda x: x.fitness)
def choice_by_fitness(sorted_population, prob):
    return choice(sorted_population, p = prob)
def fitness(indi):
    #return indi["acc_val"]/(1 - indi["acc_val"])
    return indi["fitness"]
def test(network):
    model = network.model
    model.eval()
    output = model(features, adj)
    loss_test = F.nll_loss(output[idx_test], labels[idx_test])
    acc_test = accuracy(output[idx_test], labels[idx_test])
    print("Test set results:",
          "loss= {:.4f}".format(loss_test.item()),
          "accuracy= {:.4f}".format(acc_test.item()))
    return acc_test.item()
def set_params(params):
    params["epochs"] = 200
    params["lr"] = 0.01
    params["weight_decay"] = 5e-4
    params["n_hidden"] = 16
    params["dropout"] = 0.2
    params["seed"] = 42
def print_statistics(population):
    #Mean
    f = []
    for indi in population:
        f.append(fitness(indi))
    print("Maximum fitness: ", max(f))
    print("Average fitness: ", np.mean(f))
    print("Medium fitness: ", np.median(f))
def short_print(indi):
       print("epochs: {:.2f}, n_hidden: {:.2f}, dropout: {:.3f}, weight_decay: {:.5f}, lr: {:.4f}, fitness: {:.3f}".format(
        indi["epochs"], indi["n_hidden"], indi["dropout"], indi["weight_decay"], indi["lr"], indi["fitness"]
    ))
def run_pso(values, best, optimal_sol):
    iteration = 0
    search_space = Space(1, n_particles)
    particles_vector = [Particle() for _ in range(search_space.n_particles)]
    search_space.particles = particles_vector   
    optimality_tracking = []
    while (iteration < n_iterations):
        print("=============================Iteration {0}=========================".format(iteration))
        search_space.set_pbest()
        search_space.set_gbest()
        search_space.sort_particles_by_fitness()
        search_space.print_particles()
        print('Best position: ', search_space.gbest_position)
        print('Best fitness: ', search_space.gbest_value)

        if search_space.gbest_value > best:
            best = search_space.gbest_value
            print("best = ", best)
            optimal_sol = search_space.gbest_position
        optimality_tracking.append(best)
        search_space.move_particles()
        iteration += 1
    print('opt track: ', optimality_tracking)
    values += np.array(optimality_tracking)
    print('values: ', values)
    return  values, best, optimal_sol
def simulate():
    values = np.zeros(n_iterations)
    itr = range(n_iterations)
    optimal_sol = pso_generate_individual()
    best = 0
    for s in range(simulations):
        print("===================Simulation- {0}===================".format(s))
        values, best, optimal_sol = run_pso(values, best, optimal_sol)
        print('best = ', best)
    print('optimal_sol = ', optimal_sol)
    net = NetworkInstance(**optimal_sol)
    train(net)
    s = test(net)    
    print(s)
    values /= simulations
    plt.plot(itr, values, lw = 0.5)
    plt.show()
    print(values)
if __name__ == '__main__':
    np.random.seed(cf.seed)
    torch.cuda.manual_seed(cf.seed)
    torch.manual_seed(cf.seed) #seed for training GCN, keep it the same as in original paper
    random.seed(2) # this is seed for PSO
    adj, features, labels, idx_train, idx_val, idx_test = load_data("pubmed")

    features = features.cuda()
    adj = adj.cuda()
    labels = labels.cuda()
    idx_train = idx_train.cuda()
    idx_val = idx_val.cuda()
    idx_test = idx_test.cuda()
    
    nfeat = features.shape[1]
    nclass = labels.max().item() + 1
    simulate()