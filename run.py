#! /usr/bin/env python

import argparse
import datetime

from hts.preprocess import clean_soil, clean_air, process_data, add_derivation
from hts.visualize import predict_plot
from hts.utils import moving_average, merge_data, load_raw_data
from hts.model import Model 

parser = argparse.ArgumentParser()
parser.add_argument('--type', type=str, default='lstm',
    choices=['lstm', 'gru'],
    help='RNN architecture type.')
parser.add_argument('--activation', type=str, default=None,
    choices=['tanh', 'elu', 'relu'],
    help='Activation function.')
parser.add_argument('--optimizer', type=str, default='adam',
    choices=['sgd', 'rmsprop', 'adam'],
    help='Algorithm for the minimization of loss function.')
parser.add_argument('--loss_fn', type=str, default='mse',
    choices=['mse', 'mae', 'msle'],
    help='Loss function.')
parser.add_argument('--num_layers', type=int, default=2,
    help='Number of hidden layers.')
parser.add_argument('--num_neurons', type=int, default=50, 
    help='Number of neurons per hidden layer.')
parser.add_argument('--learning_rate', type=float, default=0.01,
    help='Learning rate for the optimizer.')
parser.add_argument('--epochs', type=int, default=100,
    help='Number of training epochs.')
parser.add_argument('--batch_size', type=int, default=64,
    help='Batch size.')
parser.add_argument('--dataset', type=str, default='deep',
    choices=['deep', 'shallow'],
    help='Two current dataset generated by deep and shalow LoRa sensor.')
parser.add_argument('--split_ratio', type=float, default=0.8, 
    help='Ratio for train-test split.')
parser.add_argument('--step', type=int, default=18,
    help='Value for timestamp.')
parser.add_argument('--save_checkpoint', action='store_true',
    help='Save the best model after the training is done.')
args = parser.parse_args()

model_name_prefix = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

air_path = 'hts/data/Senzor_zraka.csv'
pressure_path = 'hts/data/DHMZ.csv'

if args.dataset == 'deep':
    soil_path = 'hts/data/Senzor_zemlje_2.csv'
    save_dir = f'saved_models/{model_name_prefix}-deep.h5'

elif args.dataset == 'shallow':
    soil_path = 'hts/data/shallow.csv'
    save_dir = f'saved_models/{model_name_prefix}-shallow.h5'


soil_raw, pressure_raw, air_raw = load_raw_data(soil_path, pressure_path, air_path)
soil = clean_soil(soil_raw, absolute=False)
pressure = clean_air(pressure_raw)
air = clean_air(air_raw)
data = merge_data(pressure, air, soil, drop_duplicate_time=True)
# data = add_derivation(data)  # uncomment if want air_humidity derivation
x_train, y_train, x_valid, y_valid, x_test, y_test, \
    scaler = process_data(data, args.step, args.split_ratio)

net = Model(
    type=args.type,
    input_shape=(x_train.shape[1], x_train.shape[2]),
    num_layers=args.num_layers,
    num_neurons=args.num_neurons
)
net.build(
    optimizer=args.optimizer, 
    learning_rate=args.learning_rate, 
    loss_fn=args.loss_fn,
    activation=args.activation
)
print('\nTrain set shape: Input {} Target {}'.format(x_train.shape, y_train.shape))
print('Valid set shape: Input {} Target {}'.format(x_valid.shape, y_valid.shape))
print('Test set shape: Input {} Target {}\n'.format(x_test.shape, y_test.shape))
model, losses = net.train(
    x_train=x_train,
    y_train=y_train,
    x_valid=x_valid,
    y_valid=y_valid,
    epochs=args.epochs,
    batch_size=args.batch_size,
    save_checkpoint=args.save_checkpoint,
    save_dir=save_dir
)
#predict_plot(model, x_train, y_train, x_valid, y_valid, x_test, y_test, scaler, losses=losses)
if not args.save_checkpoint:
    decision = input("\nSave model? [y,n] ")
    if decision == "y":
        model.save(save_dir)
    else:
        pass
