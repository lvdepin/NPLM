
import re
import argparse
import collections
import random
import numpy as np
import tensorflow as tf
import math
# Import One hot encoder here


def data_generate(filename):

	with open(filename,'r') as f:
		text = f.read()
	
	data = re.findall('\w+',text)
	return data


words = data_generate('/home/shadab/python/testing/t1')

def wordDictionary(filename):
	# Generate the data
	words = data_generate(filename)

	word_dict = collections.OrderedDict()
	
	# Index for new dictionary
	index = 0

	for word in words:
		if word not in word_dictionary:
			word_dict[word] = index
			index += 1

	return word_dict

vocabulary_size = 400

def build_dataset(words):
	
	count = [['rare', -1]]
   
	count.extend(collections.Counter(words).most_common(vocabulary_size - 1))
	dictionary = dict()
	
	for word, _ in count:
		dictionary[word] = len(dictionary)
	
	data = list()
	rare_count = 0
	for word in words:
		if word in dictionary:
			index = dictionary[word]
		else:
			index = 0  
			rare_count = rare_count + 1
		data.append(index)
	count[0][1] = rare_count
	reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
	return data, count, dictionary, reverse_dictionary

data,count,dictionary,reverse_dictionary = build_dataset(words)

data_index = 0

def generate_batch(batch_size,skip_window,num_skips):
	global data_index
	assert batch_size % num_skips == 0
	batch = np.ndarray(shape=(batch_size), dtype = np.int32)
	labels = np.ndarray(shape=(batch_size,1), dtype = np.int32)

	# Span includes the middle element and the surrounding elements. Hence plus one.
	span = 2 * skip_window + 1

	buffer = collections.deque(maxlen=span)

	for _ in xrange(span):
		buffer.append(data[data_index])
		data_index = (data_index + 1) % len(data)

	for i in range(batch_size//num_skips):
		target = skip_window # Middle element is the target
		targets_to_avoid = [ skip_window ]

		for j in range(num_skips):
			while target in targets_to_avoid: # we dont want already included word
				target = random.randint(0,span-1) # to select a random word from the buffer
			targets_to_avoid.append(target) 

			batch[i * num_skips + j] = buffer[skip_window]
			labels[i * num_skips + j] = buffer[target] # here labels are the surrounding words
		
		# This is to get the next element in the queue.
		buffer.append(data[data_index]) 
		data_index = (data_index+1) % len(data)

	return batch, labels

batch, labels = generate_batch(batch_size=8, num_skips=2, skip_window=1)

"""
print ('data :', [reverse_dictionary[d] for d in data[:8]])

for i in range(8):
	print(batch[i], reverse_dictionary[batch[i]], \
			'->', labels[i, 0], reverse_dictionary[labels[i, 0]])

"""

# Building the actual skip gram model

batch_size = 128
embedding_size = 128 # Feature vector size
skip_window = 1
num_skips = 2

# Negative sampling

valid_size = 16
valid_window = 100
valid_examples = np.random.choice(valid_window,valid_size,replace=False)
num_sampled = 64 # Number of negative samples to sample.

# Creating the computation graph

graph = tf.Graph()

with graph.as_default():


	# Inputs
	train_inputs = tf.placeholder(tf.int32,shape=[batch_size])
	train_labels = tf.placeholder(tf.int32,shape=[batch_size,1])
	valid_dataset = tf.constant(valid_examples,dtype=tf.int32)

	with tf.device('/cpu:0'):

		embeddings = tf.Variable(tf.random_uniform([vocabulary_size,embedding_size], \
												-1.0,1.0))

		embed = tf.nn.embedding_lookup(embeddings,train_inputs)

		
		# Construct the variables for the NCE loss
		nce_weights = tf.Variable(
			tf.truncated_normal([vocabulary_size, embedding_size],
							stddev=1.0 / math.sqrt(embedding_size)))
		nce_biases = tf.Variable(tf.zeros([vocabulary_size]))



		# Computing NCE loss

		loss = tf.reduce_mean(
		tf.nn.nce_loss(weights=nce_weights,
					 biases=nce_biases,
					 labels=train_labels,
					 inputs=embed,
					 num_sampled=num_sampled,
					 num_classes=vocabulary_size))

  # Construct the SGD optimizer using a learning rate of 1.0.
	optimizer = tf.train.GradientDescentOptimizer(1.5).minimize(loss)

  # Compute the cosine similarity between minibatch valid_examples and all embeddings.
	norm = tf.sqrt(tf.reduce_sum(tf.square(embeddings), 1, keep_dims=True))
	normalized_embeddings = embeddings / norm
	valid_embeddings = tf.nn.embedding_lookup(
	   normalized_embeddings, valid_dataset)
	similarity = tf.matmul(
	  valid_embeddings, normalized_embeddings, transpose_b=True)

  # Add variable initializer.
	init = tf.global_variables_initializer()

# Step 5: Begin training.
num_steps = 100001

with tf.Session(graph=graph) as session:
  # We must initialize all variables before we use them.
  init.run()
  print("Initialized")

  average_loss = 0
  for step in xrange(num_steps):
	batch_inputs, batch_labels = generate_batch(
		batch_size, num_skips, skip_window)
	feed_dict = {train_inputs: batch_inputs, train_labels: batch_labels}

	# We perform one update step by evaluating the optimizer op (including it
	# in the list of returned values for session.run()
	_, loss_val = session.run([optimizer, loss], feed_dict=feed_dict)
	average_loss += loss_val

	if step % 2000 == 0:
	  if step > 0:
		average_loss /= 2000
	  # The average loss is an estimate of the loss over the last 2000 batches.
	  print("Average loss at step ", step, ": ", average_loss)
	  average_loss = 0

	"""
	# Note that this is expensive (~20% slowdown if computed every 500 steps)
	if step % 10000 == 0:
	  sim = similarity.eval()
	  for i in xrange(valid_size):
		valid_word = reverse_dictionary[valid_examples[i]]
		top_k = 8  # number of nearest neighbors
		nearest = (-sim[i, :]).argsort()[1:top_k + 1]
		log_str = "Nearest to %s:" % valid_word
		for k in xrange(top_k):
		  close_word = reverse_dictionary[nearest[k]]
		  log_str = "%s %s," % (log_str, close_word)
		print(log_str)
	"""

final_embeddings = normalized_embeddings.eval(session=session)
print(final_embeddings)


















"""
def main():
	
	parser = argparse.ArgumentParser()

	parser.add_argument('')

	words = data_generate(args.filename)




"""









"""

import collections
import math
import numpy as np
import os
import random
import tensorflow as tf
import zipfile

import re


from six.moves import range
from six.moves.urllib.request import urlretrieve
from sklearn.manifold import TSNE


def data_generate(filename):

	with open(filename,'r') as f:
		data = re.findall('\w+',f.read())

	return data

words = data_generate('/home/shadab/python/testing/t1')

vocabulary_size = 50000

def build_dataset(words):
	# UNK token is used to denote words that are not in the dictionary
	count = [['UNK', -1]]
	# returns set of tuples (word,count) with most common 50000 words
	count.extend(collections.Counter(words).most_common(vocabulary_size - 1))
	dictionary = dict()
	# set word count for all the words to the current number of keys in the dictionary
	# in other words values act as indices for each word
	# first word is 'UNK' representing unknown words we encounter
	for word, _ in count:
		dictionary[word] = len(dictionary)
	# this contains the words replaced by assigned indices
	data = list()
	unk_count = 0
	for word in words:
		if word in dictionary:
			index = dictionary[word]
		else:
			index = 0  # dictionary['UNK']
			unk_count = unk_count + 1
		data.append(index)
	count[0][1] = unk_count
	reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
	return data, count, dictionary, reverse_dictionary

data, count, dictionary, reverse_dictionary = build_dataset(words)


print('Most common words (+UNK)', count[:5])
print('Sample data', data[:10])
del words  # Hint to reduce memory.

data_index = 0

def generate_batch(batch_size, num_skips, skip_window):
	# skip window is the amount of words we're looking at from each side of a given word
	# creates a single batch
	global data_index
	assert batch_size % num_skips == 0
	assert num_skips <= 2 * skip_window
	batch = np.ndarray(shape=(batch_size), dtype=np.int32)
	labels = np.ndarray(shape=(batch_size, 1), dtype=np.int32)
	# e.g if skip_window = 2 then span = 5
	# span is the length of the whole frame we are considering for a single word (left + word + right)
	# skip_window is the length of one side
	span = 2 * skip_window + 1 # [ skip_window target skip_window ]
	# queue which add and pop at the end
	buffer = collections.deque(maxlen=span)

	#get words starting from index 0 to span
	for _ in range(span):
		buffer.append(data[data_index])
		data_index = (data_index + 1) % len(data)

	# num_skips => # of times we select a random word within the span?
	# batch_size (8) and num_skips (2) (4 times)
	# batch_size (8) and num_skips (1) (8 times)
	for i in range(batch_size // num_skips):
		target = skip_window  # target label at the center of the buffer
		targets_to_avoid = [ skip_window ] # we only need to know the words around a given word, not the word itself

		# do this num_skips (2 times)
		# do this (1 time)
		for j in range(num_skips):
			while target in targets_to_avoid:
				# find a target word that is not the word itself
				# while loop will keep repeating until the algorithm find a suitable target word
				target = random.randint(0, span - 1)
			# add selected target to avoid_list for next time
			targets_to_avoid.append(target)
			# e.g. i=0, j=0 => 0; i=0,j=1 => 1; i=1,j=0 => 2
			batch[i * num_skips + j] = buffer[skip_window] # [skip_window] => middle element
			labels[i * num_skips + j, 0] = buffer[target]
		buffer.append(data[data_index])
		data_index = (data_index + 1) % len(data)
	return batch, labels

print('data:', [reverse_dictionary[di] for di in data[:8]])

for num_skips, skip_window in [(2, 1), (4, 2)]:
	data_index = 0
	batch, labels = generate_batch(batch_size=8, num_skips=num_skips, skip_window=skip_window)
	print('\nwith num_skips = %d and skip_window = %d:' % (num_skips, skip_window))
	print('    batch:', [reverse_dictionary[bi] for bi in batch])
	print('    labels:', [reverse_dictionary[li] for li in labels.reshape(8)])



"""