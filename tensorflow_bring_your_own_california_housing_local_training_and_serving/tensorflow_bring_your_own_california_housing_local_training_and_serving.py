# This is a sample Python program that trains a BYOC TensorFlow model, and then performs inference.
# This implementation will work on your local computer.
#
# Prerequisites:
#   1. Install required Python packages:
#       pip install boto3 sagemaker pandas scikit-learn
#       pip install 'sagemaker[local]'
#   2. Docker Desktop has to be installed on your computer, and running.
#   3. Open terminal and run the following commands:
#       docker build  -t sagemaker-tensorflow2-local container/.
########################################################################################################################

import os

import numpy as np
import pandas as pd
import sklearn.model_selection
from sagemaker.deserializers import JSONDeserializer
from sagemaker.estimator import Estimator
from sagemaker.serializers import JSONSerializer
from sklearn.datasets import *
from sklearn.preprocessing import StandardScaler

DUMMY_IAM_ROLE = 'arn:aws:iam::111111111111:role/service-role/AmazonSageMaker-ExecutionRole-20200101T000001'


def download_training_and_eval_data():
    if os.path.isfile('./data/train/x_train.npy') and \
            os.path.isfile('./data/test/x_test.npy') and \
            os.path.isfile('./data/train/y_train.npy') and \
            os.path.isfile('./data/test/y_test.npy'):
        print('Training and evaluation datasets exist. Skipping Download')
    else:
        print('Downloading training and evaluation dataset')
        data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_dir, exist_ok=True)

        train_dir = os.path.join(os.getcwd(), 'data/train')
        os.makedirs(train_dir, exist_ok=True)

        test_dir = os.path.join(os.getcwd(), 'data/test')
        os.makedirs(test_dir, exist_ok=True)

        data_set = fetch_california_housing()

        X = pd.DataFrame(data_set.data, columns=data_set.feature_names)
        Y = pd.DataFrame(data_set.target)

        # We partition the dataset into 2/3 training and 1/3 test set.
        x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(X, Y, test_size=0.33)

        scaler = StandardScaler()
        scaler.fit(x_train)
        x_train = scaler.transform(x_train)
        x_test = scaler.transform(x_test)

        np.save(os.path.join(train_dir, 'x_train.npy'), x_train)
        np.save(os.path.join(test_dir, 'x_test.npy'), x_test)
        np.save(os.path.join(train_dir, 'y_train.npy'), y_train)
        np.save(os.path.join(test_dir, 'y_test.npy'), y_test)

        print('Downloading completed')


def do_inference_on_local_endpoint(predictor):
    print(f'\nStarting Inference on endpoint (local).')

    x_test = np.load('./data/test/x_test.npy')
    y_test = np.load('./data/test/y_test.npy')

    data = {"instances": x_test[:10]}
    predictor.serializer = JSONSerializer()
    predictor.deserializer = JSONDeserializer()
    results = predictor.predict(data)['predictions']

    flat_list = [float('%.1f' % (item)) for sublist in results for item in sublist]
    print('predictions: \t{}'.format(np.array(flat_list)))
    print('target values: \t{}'.format(y_test[:10].round(decimals=1)))


def main():
    download_training_and_eval_data()

    image = 'sagemaker-tensorflow2-local'

    print('Starting model training.')
    california_housing_estimator = Estimator(
        image,
        DUMMY_IAM_ROLE,
        hyperparameters={'epochs': 10,
                         'batch_size': 64,
                         'learning_rate': 0.1},
        instance_count=1,
        instance_type="local")

    inputs = {'train': 'file://./data/train', 'test': 'file://./data/test'}
    california_housing_estimator.fit(inputs, logs=True)
    print('Completed model training')

    print('Deploying endpoint in local mode')
    predictor = california_housing_estimator.deploy(initial_instance_count=1, instance_type='local')

    do_inference_on_local_endpoint(predictor)

    print('About to delete the endpoint to stop paying (if in cloud mode).')
    predictor.delete_endpoint(predictor.endpoint_name)


if __name__ == "__main__":
    main()
