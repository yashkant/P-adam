from __future__ import absolute_import, division, print_function
import os
import sys
print(os.getcwd())
os.environ["CUDA_VISIBLE_DEVICES"]= sys.argv[1]
import tensorflow as tf
tf.enable_eager_execution()
import numpy as np
from keras.datasets import cifar10
import keras.callbacks as callbacks
import keras.utils.np_utils as kutils
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import plot_model
from resnet import Resnet 
from keras import backend as K
from keras.callbacks import ModelCheckpoint, CSVLogger
import matplotlib.pyplot as plt
import h5py

sys.path.append(os.path.dirname(os.getcwd()))
sys.path.append(os.getcwd())

print(sys.path)
from padam import Padam
from amsgrad import AMSGrad

dataset = 'cifar100'     


# Model is saved is 'model_{optim}_{dataset}_epochs{X}.h5' where X = continue_epoch 28  dataset = 'cifar100'
# Csv file is saved as 'log_{optim}_{dataset}.h5'


if dataset == 'cifar10':
    MEAN = [0.4914, 0.4822, 0.4465]
    STD_DEV = [0.2023, 0.1994, 0.2010]
    num_classes = 10
    from keras.datasets import cifar10
    (trainX, trainY), (testX, testY) = cifar10.load_data()

elif dataset == 'cifar100':
    MEAN = [0.507, 0.487, 0.441]
    STD_DEV = [0.267, 0.256, 0.276]
    num_classes = 100
    from keras.datasets import cifar100
    (trainX, trainY), (testX, testY) = cifar100.load_data()


def preprocess(t):
    paddings = tf.constant([[2, 2,], [2, 2],[0,0]])
    t = tf.pad(t, paddings, 'CONSTANT')
    t = tf.image.random_crop(t, [32, 32, 3])
    t = normalize(t) 
    return t

def normalize(t):
    t = tf.div(tf.subtract(t, MEAN), STD_DEV) 
    return t

def save_model(filepath, model):
    file = h5py.File(filepath,'w')
    weight = model.get_weights()
    for i in range(len(weight)):
        file.create_dataset('weight'+str(i),data=weight[i])
    file.close()

def load_model(filepath, model):
    file=h5py.File(filepath,'r')
    weight = []
    for i in range(len(file.keys())):
        weight.append(file['weight'+str(i)][:])
    model.set_weights(weight)
    return model 

hyperparameters = {
    'cifar10': {
        'epoch': 30,
        'batch_size': 128,
        'decay_after': 50,
        'classes':10
    },
    'cifar100': {
        'epoch': 30,
        'batch_size': 128,
        'decay_after': 50,
        'classes':100  
    },
    'imagenet': {
        'epoch': 100,
        'batch_size': 256,
        'decay_after': 30
    }
}

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

hp = hyperparameters[dataset]
epochs = hp['epoch']
batch_size = hp['batch_size']

img_rows, img_cols = 32, 32
train_size = trainX.shape[0]

trainX = trainX.astype('float32')
trainX = trainX/255
testX = testX.astype('float32')
testX = testX/255
trainY = kutils.to_categorical(trainY)
testY = kutils.to_categorical(testY)
tf.train.create_global_step()
# (trainX, trainY), (testX, testY) = (trainX[:100], trainY[:100]), (testX[:100], testY[:100])

datagen_train = ImageDataGenerator(preprocessing_function=preprocess,horizontal_flip=True)
datagen_test = ImageDataGenerator(preprocessing_function=normalize)

optim_array = ['padam']
p_values = [0.25, 0.125, 0.0625]

history = {}

for i in range(1, 3):
    if(i != 0):
        continue_training = True # Flag to continue training   
        continue_epoch = (i)*30
    else:
        continue_training = False
    
    for optimizer in optim_array:
        for p_value in p_values: 
            print('-'*40, optimizer, '-'*40)
            op = optim_params[optimizer]
            
            op['lr'] = op['lr']/(10**i)


            if optimizer == 'adamw' and dataset=='imagenet':
                op['weight_decay'] = 0.05 

            if optimizer is not 'adamw':
                model = Resnet(data_format='channels_last', classes=hp['classes'], wt_decay = op['weight_decay'])
            else:
                model = Resnet(data_format='channels_last', classes=hp['classes'], wt_decay  = 0)

            model._set_inputs(tf.zeros((batch_size, 32, 32, 3)))

            learning_rate = tf.train.exponential_decay(op['lr'], tf.train.get_global_step() * batch_size,
                                               hp['decay_after']*train_size, 0.1, staircase=True)

            logfile = 'log_'+str(p_value)+ '_' + dataset +'.csv'

            if(continue_training):
                load_model_filepath = 'model_'+str(p_value)+'_'  + dataset + '_epochs'+ str(continue_epoch)+'.h5'
                save_model_filepath = 'model_'+str(p_value)+'_'  + dataset + '_epochs'+ str(continue_epoch+epochs)+'.h5'
                model = load_model(load_model_filepath, model)
            else:
                save_model_filepath = 'model_'+str(p_value)+'_'  + dataset + '_epochs'+ str(epochs)+'.h5'


            if optimizer == 'padam':
                optim = Padam(learning_rate=learning_rate, p= p_value, beta1=op['b1'], beta2=op['b2'])

            model.compile(optimizer=optim, loss='categorical_crossentropy', metrics=['accuracy', 'top_k_categorical_accuracy'], global_step=tf.train.get_global_step())

            csv_logger = CSVLogger(logfile, append=True, separator=';')

            history[optimizer] = model.fit_generator(datagen_train.flow(trainX, trainY, batch_size = batch_size), epochs = epochs, 
                                         validation_data = datagen_test.flow(testX, testY, batch_size = batch_size), verbose=1, callbacks = [csv_logger])

            scores = model.evaluate_generator(datagen_test.flow(testX, testY, batch_size = batch_size), verbose=1)

            print("Final test loss and accuracy:", scores)
            #filepath = 'model_'+optimizer+'_'  + dataset + '.h5'
            save_model(save_model_filepath, model)
            #f.close()

#train plot
plt.figure(1)
for optimizer in optim_array:
    op = optim_params[optimizer]
    train_loss = history[optimizer].history['loss']
    epoch_count = range(1, len(train_loss) + 1)
    plt.plot(epoch_count, train_loss, color=op['color'], linestyle=op['linestyle'])
plt.legend(optim_array)
plt.xlabel('Epochs')
plt.ylabel('Train Loss')
plt.savefig('figure_'+dataset+'_train_loss.png')

#test plot
plt.figure(2)
for optimizer in optim_array:
    op = optim_params[optimizer]
    test_error = []
    for i in history[optimizer].history['val_acc']:
        test_error.append(1-i)
    epoch_count = range(1, len(test_error) + 1)
    plt.plot(epoch_count, test_error, color=op['color'], linestyle=op['linestyle'])
plt.legend(optim_array)
plt.xlabel('Epochs')
plt.ylabel('Test Error')

# plt.show()
plt.savefig('figure_'+dataset+'_test_error_top_1.png')

#test plot
plt.figure(3)
for optimizer in optim_array:
    op = optim_params[optimizer]
    test_error = []
    for i in history[optimizer].history['val_top_k_categorical_accuracy']:
        test_error.append(1-i)
    epoch_count = range(1, len(test_error) + 1)
    plt.plot(epoch_count, test_error, color=op['color'], linestyle=op['linestyle'])
plt.legend(optim_array)
plt.xlabel('Epochs')
plt.ylabel('Test Error')

plt.savefig('figure_'+dataset+'_test_error_top_5.png')
