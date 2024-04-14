---
citekey: wunderlichDemonstratingAdvantagesNeuromorphic2019
aliases:
- "Wunderlich et al. (2019) Demonstrating Advantages of Neuromorphic Computation"
title: "Demonstrating Advantages of Neuromorphic Computation: A Pilot Study" 
authors:
- Timo Wunderlich 
- Akos F. Kungl 
- Eric Müller 
- Andreas Hartel 
- Yannik Stradmann 
- Syed Ahmed Aamir 
- Andreas Grübl 
- Arthur Heimbrecht 
- Korbinian Schreiber 
- David Stöckel 
- Christian Pehle 
- Sebastian Billaudelle 
- Gerd Kiene 
- Christian Mauch 
- Johannes Schemmel 
- Karlheinz Meier 
- Mihai A. Petrovici  
year: 2019
item-type: Journal Article
publisher: "Frontiers in Neuroscience"
tags:
- brainscales
- mixed-signal
- neuromorphic-computing
- plasticity
- Reinforcement-Learning
- Spiking-neural-network-(SNN)
- STDP
- exported
doi: https://doi.org/10.3389/fnins.2019.00260
cssclasses: 
- literature-note
attachments:
- 
- /home/paolo/zotero_data/storage/8Z9TLYC2/Wunderlich_et_al-2019-Demonstrating_Advantages_of_Neuromorphic_Computation.pdf
---
%% begin notes %%
## Key takeaways

- mostly about technical side
- uses reinforcement learning with reward-modulated stdp
- NEST implementation of game + visualization is available in zotero linked document

## Connections

- 

%% end notes %%

> [!info]- Info 🔗 [**Zotero**](zotero://select/groups/5439920/items/B9X27LI3) | [**DOI**](https://doi.org/10.3389/fnins.2019.00260) | [**PDF-1**](file:////home/paolo/zotero_data/storage/8Z9TLYC2/Wunderlich_et_al-2019-Demonstrating_Advantages_of_Neuromorphic_Computation.pdf)
>
>**Bibliography**: [1]T. Wunderlich _et al._, “Demonstrating Advantages of Neuromorphic Computation: A Pilot Study,” _Front. Neurosci._, vol. 13, Mar. 2019, doi: [10.3389/fnins.2019.00260](https://doi.org/10.3389/fnins.2019.00260).
> 
> **Authors**::  [[03 - Source notes/People/Timo Wunderlich|Timo Wunderlich]],  [[03 - Source notes/People/Akos F. Kungl|Akos F. Kungl]],  [[03 - Source notes/People/Eric Müller|Eric Müller]],  [[03 - Source notes/People/Andreas Hartel|Andreas Hartel]],  [[03 - Source notes/People/Yannik Stradmann|Yannik Stradmann]],  [[03 - Source notes/People/Syed Ahmed Aamir|Syed Ahmed Aamir]],  [[03 - Source notes/People/Andreas Grübl|Andreas Grübl]],  [[03 - Source notes/People/Arthur Heimbrecht|Arthur Heimbrecht]],  [[03 - Source notes/People/Korbinian Schreiber|Korbinian Schreiber]],  [[03 - Source notes/People/David Stöckel|David Stöckel]],  [[03 - Source notes/People/Christian Pehle|Christian Pehle]],  [[03 - Source notes/People/Sebastian Billaudelle|Sebastian Billaudelle]],  [[03 - Source notes/People/Gerd Kiene|Gerd Kiene]],  [[03 - Source notes/People/Christian Mauch|Christian Mauch]],  [[03 - Source notes/People/Johannes Schemmel|Johannes Schemmel]],  [[03 - Source notes/People/Karlheinz Meier|Karlheinz Meier]],  [[03 - Source notes/People/Mihai A. Petrovici|Mihai A. Petrovici]]
> 
> **Tags**: #brainscales, #mixed-signal, #neuromorphic-computing, #plasticity, #Reinforcement-Learning, #Spiking-neural-network-(SNN), #STDP, #exported
> 
> **Collections**:: [[thesis]]


> [!abstract]-
> 
> Neuromorphic devices represent an attempt to mimic aspects of the brain's architecture and dynamics with the aim of replicating its hallmark functional capabilities in terms of computational power, robust learning and energy efficiency. We employ a single-chip prototype of the BrainScaleS 2 neuromorphic system to implement a proof-of-concept demonstration of reward-modulated spike-timing-dependent plasticity in a spiking network that learns to play a simplified version of the Pong video game by smooth pursuit. This system combines an electronic mixed-signal substrate for emulating neuron and synapse dynamics with an embedded digital processor for on-chip learning, which in this work also serves to simulate the virtual environment and learning agent. The analog emulation of neuronal membrane dynamics enables a 1000-fold acceleration with respect to biological real-time, with the entire chip operating on a power budget of 57 mW. Compared to an equivalent simulation using state-of-the-art software, the on-chip emulation is at least one order of magnitude faster and three orders of magnitude more energy-efficient. We demonstrate how on-chip learning can mitigate the effects of fixed-pattern noise, which is unavoidable in analog substrates, while making use of temporal variability for action exploration. Learning compensates imperfections of the physical substrate, as manifested in neuronal parameter variability, by adapting synaptic weights to match respective excitability of individual neurons.
> 

> [!quote]- Citations
> 
> ```query
> content: "@wunderlichDemonstratingAdvantagesNeuromorphic2019" -file:@wunderlichDemonstratingAdvantagesNeuromorphic2019
> ```

___
## Reading notes

%% begin annotations %%


*Imported on [[2024-04-04]] at 15:34*
- & proof-of-concept demonstration of reward-modulated spike-timing-dependent plasticity in a spiking network that learns to play a simplified version of the Pong video game by smooth pursuit. [(p. 1)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=1&annotation=RS9IL4KB)
### introduction
- & link between reinforcement learning paradigms used in machine learning and reinforcement learning in the brain (for a review, see Niv, 2009). The neuromodulator dopamine was found to convey a reward prediction error, akin to the temporal difference error used in reinforcement learning methods (Schultz et al., 1997; Sutton and Barto, 1998). Neuromodulated plasticity can be modeled using three-factor learning rules (Frémaux et al., 2013; Frémaux and Gerstner, 2015), where the synaptic weight update depends not only on the learning rate and the pre- and post-synaptic activity but also on a third factor, representing the neuromodulatory signal, which can be a function of reward, enabling reinforcement learning. [(p. 2)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=2&annotation=U8KJHVMH)
- & showing how an agent controlled by a spiking neural network (SNN) learns to solve a smooth pursuit task via reinforcement learning in a fully embedded perceptionaction loop that simulates the classic Pong video game on the BSS2 prototype [(p. 2)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=2&annotation=H9KJU99M)
- & As the number of neurons (32) and synapses (1,024) on the prototype chip constrain the complexity of solvable learning tasks, the agent’s task in this work is simple smooth pursuit without anticipation. [(p. 2)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=2&annotation=5BACK7C9)
### materials and methods
#### the brainscales 2 neuromorphic prototype chip
##### neurons and synapses
- & the analog neuronal circuits are designed to have similar dynamics compared to their biological counterparts, making use of the physical characteristics of the underlying substrate. [(p. 2)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=2&annotation=6H2JXUXQ)
- & Leaky Integrate-and-Fire (LIF) model [(p. 2)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=2&annotation=T9NZSHWB)
- & the hardware operates with a speed-up factor of 103 compared to biology [(p. 3)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=3&annotation=NU2CB98L)
- & six parameters: membrane time constant τmem, synaptic time constant τsyn, refractory period τref, resting potential vleak, threshold potential vthresh, reset potential vreset [(p. 3)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=3&annotation=XQCJJHGF)
- & in order to accurately map user-defined LIF time constants to hardware parameters, neuron circuits are calibrated individually. Using this calibration data reduces deviations from target values to < 5 % [(p. 3)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=3&annotation=AQNXHS3V)
##### plasticity processing unit
##### correlation measurement at the synapses
- & Every synapse in the syna [(p. 4)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=4&annotation=UVUDLRCQ)
#### types of noise on bss2
#### reinforcement learning with reward-modulated stdp
- & The learning rule used in this work, Reward-modulated SpikeTiming Dependent Plasticity (R-STDP) [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=IDF384XE)
- **They're very confident in stating this!**:
	- & The reward mechanism in R-STDP is biologically inspired: the phasic activity of dopamine neurons in the brain was found to encode expected reward (Schultz et al., 1997; Hollerman and Schultz, 1998; Bayer and Glimcher, 2005) and dopamine concentration modulates STDP [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=PRASDSCJ)
- & R-STDP and similar reward-modulated Hebbian learning rules have been used to solve a variety of learning tasks in simulations, such as reproducing temporal spike patterns and spatio-temporal trajectories (Farries and Fairhall, 2007; Vasilaki et al., 2009; Frémaux et al., 2010), reproducing the results of classical conditioning (Izhikevich, 2007), making a recurrent neural network exhibit specific periodic activity and working-memory properties (Hoerzer et al., 2014) and reproducing the seminal biofeedback experiment by Fetz and Baker [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=VWV7YYE5)
- & We employ the following form of discrete weight updates using R-STDP: [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=FAGXHBHZ)

> [!cite]+ Image [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=9Q242U5Z)
> ![[media/zotero/wunderlichDemonstratingAdvantagesNeuromorphic2019/wunderlichDemonstratingAdvantagesNeuromorphic2019-5-x375-y270.png]]

- & where β is the learning rate, R is the reward, b is a baseline and eij is the STDP eligibility trace which is a function of the pre- and post-synaptic spikes of the synapse connecting neurons i and j. The choice of the baseline reward b is critical: a nonzero offset introduces an admixture of unsupervised learning via the unmodulated STDP term, and choosing b to be the taskspecific expected reward b = 〈R〉task leads to weight updates that capture the covariance of reward and synaptic activity (Frémaux and Gerstner, 2015): [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=UTGYUNGE)

> [!cite]+ Image [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=WGQAP3YU)
> ![[media/zotero/wunderlichDemonstratingAdvantagesNeuromorphic2019/wunderlichDemonstratingAdvantagesNeuromorphic2019-5-x309-y138.png]]

- & This setting, which we also employ in our experiments, makes R-STDP a statistical learning rule in the sense that it captures correlations of joint pre- and post-synaptic activity and reward; this information is collected over many trials of any single learning task. The expected reward may be estimated as a moving average of the reward over the last trials of that specific task; [(p. 5)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=5&annotation=HHSEEK7C)
#### learning task and simulated environment
- & The neural network consists of two 32-unit layers which are initialized with all-to-all feed-forward connections [(p. 6)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=6&annotation=Y76UVZTB)
- & The action neurons’ spike counts ρi are used to determine the paddle movement: the unit with the highest number of output spikes j = argmaxi(ρi) determines the paddle’s target column j, toward which it moves with constant velocity vp [(p. 6)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=6&annotation=99UBYGB6)
- & the reward R is calculated based on the distance between the target column j and the current column of the ball, k: [(p. 6)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=6&annotation=XIZVNPVP)

> [!cite]+ Image [(p. 6)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=6&annotation=QJCS22GU)
> ![[media/zotero/wunderlichDemonstratingAdvantagesNeuromorphic2019/wunderlichDemonstratingAdvantagesNeuromorphic2019-6-x346-y424.png]]


> [!cite]+ Image [(p. 6)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=6&annotation=QXZZVMCF)
> ![[media/zotero/wunderlichDemonstratingAdvantagesNeuromorphic2019/wunderlichDemonstratingAdvantagesNeuromorphic2019-6-x48-y156.png]]

#### software simulation with nest
### results
#### learning performance

> [!cite]+ Image [(p. 9)](zotero://open-pdf/groups/5439920/items/8Z9TLYC2?page=9&annotation=CUES6RXW)
> ![[media/zotero/wunderlichDemonstratingAdvantagesNeuromorphic2019/wunderlichDemonstratingAdvantagesNeuromorphic2019-9-x36-y478.png]]
%% end annotations %%

`BUTTON[update-litnote-headers]`

%% Import Date: 2024-04-04T15:34:13.262+02:00 %%
