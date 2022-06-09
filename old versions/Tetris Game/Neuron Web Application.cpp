#include <iostream>
#include <fstream>
#include <time.h>
#include <cmath>
#include <random>

using namespace std;

float *scalarDot(float ** input_layer, float synweights[]) {
	float* scalarDoted = new float [4];
	for (int i = 0; i < 4; i++) {
		scalarDoted[i] = input_layer[i][0] * synweights[0] + input_layer[i][1] * synweights[1] + input_layer[i][2] * synweights[2];
	}
	return scalarDoted;
}

float *sigmoid(float * scalarDoted) {
	float* newOutput = new float [4];
	for (int i = 0; i < 4; i++) newOutput[i] = 1 / (1 + exp(-scalarDoted[i]));
	return newOutput;
}

float genWeight() {
	return -1 + static_cast <float> (rand()) / (static_cast <float> (RAND_MAX / (1 - -1)));
}

void backPropogation(int counter, float **training_inputs, float synweights[], float training_outputs[]) {
	float** input_layer = training_inputs;
	for (int i = 0; i < counter; i++) {
		float* outputs = sigmoid(scalarDot(input_layer, synweights));
		float* error = new float[4];
		for (int i = 0; i < 4; i++) error[i] = training_outputs[i] - outputs[i];
		float* adjustments = new float[3];
	}
	cout << endl << "Weights after learning: " << synweights;
	cout << endl << "Result after learning: ";
}

int main() {
	int N, M;
	N = 3;
	M = 4;
	float** training_inputs;
	training_inputs = new float* [M];
	for (int i = 0; i < M; i++) training_inputs[i] = new float[N];

	training_inputs[0][0] = 0;
	training_inputs[0][1] = 1;
	training_inputs[0][2] = 0;

	training_inputs[1][0] = 1;
	training_inputs[1][1] = 1;
	training_inputs[1][2] = 0;

	training_inputs[2][0] = 1;
	training_inputs[2][1] = 0;
	training_inputs[2][2] = 0;

	training_inputs[3][0] = 0;
	training_inputs[3][1] = 1;
	training_inputs[3][2] = 1;

	float training_outputs[4] = {
		{0}, {1}, {1}, {0}
	};

	float synweights[3] = { genWeight(), genWeight(), genWeight() };
	cout << "Generated weights: " << endl;
	for (int i = 0; i < 3; i++) cout << synweights[i] << endl;
	backPropogation(2, training_inputs, synweights, training_outputs);
}