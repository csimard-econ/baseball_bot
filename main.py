
from datetime import date
import os
from functions import *
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense

# preliminaries
data_dir = os.getcwd() + os.sep + 'data' + os.sep
pull_data = True

# pull data
if pull_data:
    start_date = date(2021, 4, 1)
    end_date = date(2021, 9, 30)
    ma = 20
    baseball_data = get_training_data(start_date, end_date, ma)
    baseball_data.to_pickle(data_dir + 'baseball_data.pkl')

# compute pythagorean expectation
baseball_data = pd.read_pickle(data_dir + 'baseball_data.pkl')
baseball_data['PE_team'] = baseball_data['R_hit_team']**2 / (baseball_data['R_hit_team']**2 + ((baseball_data['ERA_pitch_team']/9)*baseball_data['IP_pitch_team'])**2)
baseball_data['PE_opponent'] = baseball_data['R_hit_opponent']**2 / (baseball_data['R_hit_opponent']**2 + ((baseball_data['ERA_pitch_opponent']/9)*baseball_data['IP_pitch_opponent'])**2)

# neural network setup
training_date = date(2021, 8, 30).strftime("%Y-%m-%d")
features = ['wRC+_hit_team', 'FIP_pitch_team', 'PE_team',
            'wRC+_hit_opponent', 'FIP_pitch_opponent', 'PE_opponent']
y_train = baseball_data['win'][baseball_data['date'] <= training_date]
y_test = baseball_data['win'][baseball_data['date'] > training_date]
X_train = baseball_data[features][baseball_data['date'] <= training_date]
X_test = baseball_data[features][baseball_data['date'] > training_date]

# dummy variables
#X_train = pd.get_dummies(X_train, columns=['team'], drop_first=True)
#X_test = pd.get_dummies(X_test, columns=['team'], drop_first=True)

# define model
n_features = X_train.shape[1]
model = Sequential()
model.add(Dense(4, activation='relu', kernel_initializer='he_normal', input_shape=(n_features,)))
model.add(Dense(2, activation='relu', kernel_initializer='he_normal'))
model.add(Dense(1, activation='sigmoid'))
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# fit model
model.fit(X_train, y_train, epochs=150, batch_size=32, verbose=0)
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print('Test Accuracy: %.3f' % acc)

# temp
temp = 1
