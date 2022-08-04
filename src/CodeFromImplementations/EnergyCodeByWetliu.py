#The code here is what was used in the github repo for the paper: https://arxiv.org/pdf/2010.03759.pdf
# Repo: https://github.com/wetliu/energy_ood
import torch
import torch.nn.functional as F
import numpy as np

#I have added this section because the original used an arguement parser to define args and I do not need that (or know how to use it)
class consts:
    def __init__(self,score="energy",m_in=-1,m_out=0,Temp=0.00001):
        self.score = score
        #the defaults for the m_in and m_out are NOT the defaults in the arguement parser (those were too big and made the model unable to train)
        self.m_in=m_in
        self.m_out = m_out
        self.T = Temp
args = consts()

#I want some way to graph changes in temp:
def setTemp(new_temp):
    args.T = new_temp

#this code was from line 112 of energy_ood/CIFAR/test.py
to_np = lambda x: x.data.cpu().numpy()


def energyLossMod(loss,x,in_set):
    #This code was lines 192-196 of energy_ood/CIFAR/train.py and it is an addition to the training loss to account for energy.

    # cross-entropy from softmax distribution to uniform distribution
    if args.score == 'energy':
        Ec_out = -torch.logsumexp(x[len(in_set[0]):], dim=1)
        Ec_in = -torch.logsumexp(x[:len(in_set[0])], dim=1)
        loss += 0.1*(torch.pow(F.relu(Ec_in-args.m_in), 2).mean() + torch.pow(F.relu(args.m_out-Ec_out), 2).mean())


    return loss


def energyScoreCalc(_score, output):
    #This code was from lines 133-134 of energy_ood/CIFAR/test.py
    if args.score == 'energy':
                    _score.append(-to_np((args.T*torch.logsumexp(output / args.T, dim=1))))
    

    return _score
