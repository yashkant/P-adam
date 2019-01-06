import matplotlib.pyplot as plt
import pandas as pd

optim_params = {
    'padam': {
        'weight_decay': 0.0005,
        'lr': 0.1,
        'p': 0.125,
        'b1': 0.9,
        'b2': 0.999, 
        'color': 'darkred',
        'linestyle':'-'
    },
    'adam': {
        'weight_decay': 0.0001,
        'lr': 0.001,
        'b1': 0.9,
        'b2': 0.99,
        'color': 'orange',
        'linestyle':'--'
    },
    'adamw': {
        'weight_decay': 0.025,
        'lr': 0.001,
        'b1': 0.9,
        'b2': 0.99,
        'color': 'magenta',
        'linestyle':'--'
    },
    'amsgrad': {
        'weight_decay': 0.0001,
        'lr': 0.001,
        'b1': 0.9,
        'b2': 0.99,
        'color' : 'darkgreen',
        'linestyle':'-.'
    },
    'sgd': {
        'weight_decay': 0.0005,
        'lr': 0.1,
        'm': 0.9,
        'color': 'blue',
        'linestyle':'-'
    }
}

parameter = 'loss' #loss;val_acc;val_top_k_categorical_accuracy
optimizers = ['adam', 'adamw', 'sgd', 'amsgrad', 'padam']
dataset = 'cifar10'
files = []

label = {'loss':'Train Loss', 'val_acc':'Test Error', 'val_top_k_categorical_accuracy':'Test Error(top 5)'}

for optim in optimizers:
    files.append('log_' + optim + '_'+ dataset + '.csv')

data = pd.DataFrame()

for f in range(len(files)):
    df = pd.read_csv(files[f], delimiter = ';')
    data[optimizers[f]] = df[parameter]

if parameter == 'val_acc' or parameter == 'val_top_k_categorical_accuracy':
    data = 1-data
    
plt.figure()
for optimizer in optimizers:
    op = optim_params[optimizer]
    data[optimizer].plot(color=op['color'], linestyle=op['linestyle'])

plt.legend(loc='best')
plt.xlabel('Epochs')
plt.ylabel(label[parameter])
plt.ylim(top=1)
#plt.show()
plt.savefig('figure_'+dataset+'_'+label[parameter]+'.png')