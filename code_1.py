class Network:
	def __init__(self):
		"""
		Initializes a neural network by defining its layers and loss functions, leaving
		self.layers as an empty list and setting self.loss and self.loss_prime to null
		references.

		"""
		self.layers = []
		self.loss = None
		self.loss_prime = None

	# add layer to network
	def add(self, layer):
		self.layers.append(layer)

	# set loss to use
	def use(self, loss, loss_prime):
		"""
		Updates the instance's `loss` and `loss_prime` attributes with provided values.

		Args:
		    loss (int): actual loss of the model being optimized.
		    loss_prime (`object`): additional loss that is used to update the model's
		        parameters during training.
		        
		        		- `loss`: The input loss is assigned to the `self.loss` attribute.
		        		- `loss_prime`: The deserialized input `loss_prime` is assigned to the
		        `self.loss_prime` attribute.

		"""
		self.loss = loss
		self.loss_prime = loss_prime

	# predict output for given input
	def predict(self, input_data):
		# sample dimension first
		"""
		Takes a sequence of input data as input and runs it through the network's layers,
		producing an output sequence.

		Args:
		    input_data (`object`.): 1D numpy array or tensor that the network will operate
		        on, and its size is passed as an integer argument to the function.
		        
		        		- `len(input_data)` is the number of samples in the input data.
		        		- `input_data` itself is a list or numpy array containing the input
		        values for the network.
		        
		        	The function loops over each sample in `input_data`, applies the forward
		        propagation for each layer in the network, and appends the output value
		        to a new list called `result`.

		Returns:
		    array of numbers: a list of predicted outputs for the given input data.
		    
		    	1/ `result`: A list of outputs predicted by the neural network, where each
		    element in the list is the output of one iteration over the input data.
		    	2/ Each output in the list has the following properties:
		    			- It is a numpy array, representing the predicted value for the corresponding
		    input sample.
		    			- It has the same shape as the input data, indicating the number of
		    features or dimensions in the output.
		    			- The values in the array are float numbers, representing the predicted
		    probabilities or values for each output feature.

		"""
		samples = len(input_data)
		result = []

		# run network over all samples
		for i in range(samples):
			# forward propagation
			output = input_data[i]
			for layer in self.layers:
				output = layer.forward_propagation(output)
			result.append(output)

		return result

	# train the network
	def fit(self, x_train, y_train, epochs, learning_rate):
		# sample dimension first
		"""
		Trains a neural network using a given set of input and output data, iterating
		through a specified number of epochs, computing the average loss per sample at
		each iteration, and displaying the average loss after each epoch.

		Args:
		    x_train (list): training data for which the model's performance will be
		        evaluated through the forward and backward propagation of its layers,
		        and the computation of the loss and average error.
		    y_train (float): targets or labels of the training data that are to be used
		        for computing the loss and performing backward propagation during each
		        iteration of the training loop.
		    epochs (int): number of training iterations to perform in the neural network's
		        training loop.
		    learning_rate (scalar.): learning rate of the neural network's weights update
		        at each iteration of the training loop.
		        
		        		- Learning rate is an hyperparameter that controls how quickly the
		        weights are updated during training.
		        		- It can take different forms such as a scalar value, a vector of
		        values for multiple hyperparameters, or a learned hyperparameter from a
		        previous layer.
		        		- The learning rate can have various attributes, such as:
		        		+ Decaying: The learning rate may decrease over time to prevent
		        overshooting during training. This is commonly achieved through exponentially
		        decaying the learning rate with each iteration.
		        		+ Adaptive: The learning rate can adapt based on certain conditions,
		        such as the convergence of a layer or the magnitude of the gradients.
		        		+ Bias: Some learning rates have a fixed bias added to the main learning
		        rate.
		        		+ Multi-step: The learning rate can be split into multiple smaller
		        learning rates for each step of the training process.
		        
		        	Note: These properties and attributes may not be present in all instances
		        of the `learning_rate` input, depending on its specific definition and
		        usage in the code.

		"""
		samples = len(x_train)

		# training loop
		for i in range(epochs):
			err = 0
			for j in range(samples):
				# forward propagation
				output = x_train[j]
				for layer in self.layers:
					output = layer.forward_propagation(output)

				# compute loss (for display purpose only)
				err += self.loss(y_train[j], output)

				# backward propagation
				error = self.loss_prime(y_train[j], output)
				for layer in reversed(self.layers):
					error = layer.backward_propagation(error, learning_rate)

			# calculate average error on all samples
			err /= samples
			print("epoch %d/%d   error=%f" % (i + 1, epochs, err))
