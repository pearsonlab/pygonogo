/*
 * Reconstruct unstrobed words from bit events.
 *
 * Copyright (C) 2010-2011 Huang Xin
 *
 * See LICENSE.TXT that came with this file.
 *
 */

#include "Python.h"
#include "numpy/arrayobject.h"

#define IND1_int(a, i) *((int *)(a->data + i*a->strides[0]))
#define IND1_float(a, i) *((float *)(a->data + i*a->strides[0]))
#define IND2_float(a, i, j) *((float *)(a->data + i*a->strides[0] + j*a->strides[1]))

static char reconstruct_word_32__doc__[] =
"Plexon._unstrobed_word.reconstruct_word_32(WORD_BITS,bits_num,unstrobed_bits,words_buffer,timestamps_buffer) -> words_count";

// construct_word(WORD_BITS,bits_num,unstrobed_bits,words_buffer,timestamps_buffer):

static PyObject * reconstruct_word_32(PyObject *self, PyObject *args){
	int i, bit, bits_num, word, words_count, indices_sum, WORD_BITS;
	int bits_indices[32];
	int word_bits[32], bits_count;
	float oldest_timestamps[32], word_timestamp;
	PyArrayObject *unstrobed_bits, *words_buffer, *timestamps_buffer;

	words_count = indices_sum = 0;


	if (!PyArg_ParseTuple(args, "iiO!O!O!", &WORD_BITS,
										    &bits_num,
										    &PyArray_Type, &unstrobed_bits,
										    &PyArray_Type, &words_buffer,
										    &PyArray_Type, &timestamps_buffer))
		return NULL;

	if (WORD_BITS != 32 || WORD_BITS != unstrobed_bits->dimensions[0]){
		PyErr_Format(PyExc_ValueError, \
					"The first dimension of unstrobed_bits is not %d", WORD_BITS);
		return NULL;
	}

	if (unstrobed_bits->nd != 2 || unstrobed_bits->descr->type_num != PyArray_FLOAT) {
		PyErr_Format(PyExc_ValueError, \
					"The input unstrobed_bits array is %d-dimensional or not of dtype float32", unstrobed_bits->nd);
		return NULL;
	}

	if (words_buffer->nd != 1 || words_buffer->descr->type_num != PyArray_INT32) {
		PyErr_Format(PyExc_ValueError, \
					"The input words_buffer array is %d-dimensional or not of dtype int", words_buffer->nd);
		return NULL;
	}

	if (timestamps_buffer->nd != 1 || timestamps_buffer->descr->type_num != PyArray_FLOAT) {
		PyErr_Format(PyExc_ValueError, \
					"The input timestamps_buffer array is %d-dimensional or not of dtype float32", timestamps_buffer->nd);
		return NULL;
	}

	for (i = 0; i < WORD_BITS; i++){
		bits_indices[i] = 0;
		oldest_timestamps[i] = IND1_float(unstrobed_bits,i);
	}

	while (indices_sum < bits_num){
		word = 0;
		word_timestamp = oldest_timestamps[0];
		bits_count = 1;
		word_bits[0] = 0;
		for (i = 1; i < WORD_BITS; i++){
			if (word_timestamp > oldest_timestamps[i]){
				word_timestamp = oldest_timestamps[i];
				word_bits[0] = i;		// the first bit index of this timestamp
				bits_count = 1;
			}
			else if (word_timestamp == oldest_timestamps[i]){
				word_bits[bits_count] = i;
				bits_count += 1;
			}
		}
		for (i = 0; i < bits_count; i++){
			bit = word_bits[i];
			word = word + (1 << bit);
			bits_indices[bit] += 1;
			oldest_timestamps[word_bits[i]] = IND2_float(unstrobed_bits,bit,bits_indices[bit]);
		}
		indices_sum += bits_count;
		IND1_int(words_buffer,words_count) = word;
		IND1_float(timestamps_buffer,words_count) = word_timestamp;
		words_count += 1;
	}
	return Py_BuildValue("i",words_count);
}

static PyMethodDef _unstrobed_word_methods[] = {
		{ "reconstruct_word_32", reconstruct_word_32, METH_VARARGS, reconstruct_word_32__doc__},
		{ NULL, NULL} /* sentinel */
};

DL_EXPORT(void)
init_unstrobed_word(void) {
		Py_InitModule("_unstrobed_word", _unstrobed_word_methods);
		import_array();
		return;
}
