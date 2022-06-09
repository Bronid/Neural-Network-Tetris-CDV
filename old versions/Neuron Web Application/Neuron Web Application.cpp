#include <iostream>
#include <fstream>
#include <time.h>
#include <cmath>
#include <random>
#include <iomanip>

using namespace std;

float** new2DMatrix(const int m, const int n)
{
	float** arr = new float* [m];
	for (int i = 0; i < m; ++i) arr[i] = new float[n];
	return arr;
}

void delete2DArray(float** arr, const int m)
{
	for (int i = 0; i < m; ++i) delete[] arr[i];
	delete[] arr;
}

float** newTransposeMatrix(float** matrix, const int m, const int n)
{
	float** res = new2DMatrix(n, m);

	for (int i = 0; i < n; i++)
		for (int j = 0; j < m; j++)
			res[i][j] = matrix[j][i];

	return res;
}

void print2DMatrix(float** arr, const int m, const int n)
{
	cout << endl;
	for (int i = 0; i < m; i++)
	{
		for (int j = 0; j < n; j++) cout << setw(4) << arr[i][j];
		cout << '\n';
	}
}

float *scalarWeightsDot(float ** input_layer, float *synweights, int n) {
	float* scalarDoted = new float [n];
	for (int i = 0; i < n; i++) {
		scalarDoted[i] = input_layer[i][0] * synweights[0] + input_layer[i][1] * synweights[1] + input_layer[i][2] * synweights[2];
	}
	return scalarDoted;
}

float* scalarAdjustmentsDot(float** matrix, float *error, float* outputs) {
	float* scalarDoted = new float[3];
	float* newMatrix = new float[4];
	for (int i = 0; i < 4; i++) {
		newMatrix[i] = error[i] * (outputs[i] * (1 - outputs[i]));
	}

	for (int i = 0; i < 3; i++) {
		scalarDoted[i] = matrix[i][0] * newMatrix[0] + matrix[i][1] * newMatrix[1] + matrix[i][2] * newMatrix[2] + matrix[i][3] * newMatrix[3];
	}
	return scalarDoted;
}

float *sigmoid(float * scalarDoted, int n) {
	float* newOutput = new float [4];
	for (int i = 0; i < n; i++) newOutput[i] = 1 / (1 + exp(-scalarDoted[i]));
	return newOutput;
}

float genWeight() {
	return -1 + static_cast <float> (rand()) / (static_cast <float> (RAND_MAX / (1 - -1)));
}

void backPropogation(int counter, float **training_inputs, float *synweights, float training_outputs[]) {
	float** input_layer = training_inputs;
	float* endOutputs = new float[3];
	for (int i = 0; i < counter; i++) {
		float* outputs = sigmoid(scalarWeightsDot(input_layer, synweights, 4), 4);
		float* error = new float[4];
		for (int i = 0; i < 4; i++) error[i] = training_outputs[i] - outputs[i];
		float* adjustments = new float[3];
		adjustments = scalarAdjustmentsDot(newTransposeMatrix(input_layer, 4, 3), error, outputs);
		for (int i = 0; i < 3; i++) synweights[i] += adjustments[i];
		if (i == counter - 1) {
			for (int i = 0; i < 4; i++) endOutputs[i] = outputs[i];
		}
	}
	cout << endl << "Weights after learning: ";
	for (int i = 0; i < 3; i++) cout << synweights[i] << " ";
	cout << endl << "Result after learning: ";
	for (int i = 0; i < 4; i++) cout << endOutputs[i] << " ";
}

int main() {
	int m, n;
	m = 4;
	n = 3;
	float** training_inputs = new2DMatrix(m, n);

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

	float* synweights = new float[3];
	for (int i = 0; i < 3; i++) synweights[i] = genWeight();
	cout << "Generated weights: " << endl;
	for (int i = 0; i < 3; i++) cout << synweights[i] << endl;
	backPropogation(100000, training_inputs, synweights, training_outputs);
	float ** newInputs = new2DMatrix(1, 3);
	for (int i = 0; i < 3; i++) {
		cout << endl << "Write " << i + 1 << " number: ";
		cin >> newInputs[0][i];
	}
	float * newOutput = sigmoid(scalarWeightsDot(newInputs, synweights, 1), 1);
	cout << endl << "New situation: " << newOutput[0];
}