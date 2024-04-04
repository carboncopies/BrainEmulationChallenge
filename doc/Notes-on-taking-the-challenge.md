# Notes on taking the challenge

## First interaction with the challenge taker

1. Send acquired data sets for the BS and SC XOR ground-truth systems. Actually, just make this public. The website will have the data and a description of how to take the challenge.


## Example of challenge participant taking the challenge

The participant works with high resolution microscopy data, primarily EM, and has a method of reconstruction that involves identifying neurons and neural processes in EM data, recreating a supposed connectome from that. The participant's method then involves simply counting the pixels of a visible postsynaptic density (PSD) and the number of such PSDs between two neurons to establish a candidate strength of the connection. The participant's method then compares all candidate connection strengths to determine relative strengths and from that establishes a range of supposed cumulative conductances between each pair of neurons. The participant's method assumes that the visible volume of a neuron found in the EM data set can be used to identify it as either a principal neuron or an interneuron. The method assumes that axons have a single root while dendrites fan out early. The participant wishes to use this method to participate in the challenge. The participant therefore seeks challenge EM data sets to work with.


### Participant inspects the EM data stack

The detailed process is documented in a slide deck at https://docs.google.com/presentation/d/1AYN8wK_nefLtiEa6phz2c5jocO1DXzqfaLIpgLDgRKw/edit?usp=sharing

The participants submits a model description as follows:

```
{
	"model": "WBE-challenge-submission",
	"neurons": [
		{
			"name": "A",
			"type": "principal"
		},
		{
			"name": "B",
			"type": "principal"
		},
		{
			"name": "C",
			"type": "principal"
		},
		{
			"name": "D",
			"type": "principal"
		},
		{
			"name": "E",
			"type": "principal"
		},
		{
			"name": "F",
			"type": "interneuron"
		},
		{
			"name": "G",
			"type": "interneuron"
		}
	]
	"connections": [
		{
			"type": "AMPA",
			"weight": "1.0"
			"from": "A",
			"to": "E",
		},
		{
			"type": "AMPA",
			"weight": "1.0"
			"from": "B",
			"to": "D",
		},
		{
			"type": "AMPA",
			"weight": "1.0"
			"from": "A",
			"to": "F",
		},
		{
			"type": "AMPA",
			"weight": "1.0"
			"from": "B",
			"to": "G",
		},
		{
			"type": "AMPA",
			"weight": "1.0"
			"from": "D",
			"to": "C",
		},
		{
			"type": "GABA",
			"weight": "1.0"
			"from": "F",
			"to": "D",
		},
		{
			"type": "GABA",
			"weight": "1.0"
			"from": "G",
			"to": "E",
		},
	]
}
```

