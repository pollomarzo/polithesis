---
marp: true
theme: gaia
style: |
    .align-right{
        text-align: right;
    }
    .align-left{
        text-align: left;
    }
    .text-small {
        font-size: 0.75em;
    }
    .twocols {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
    }
    .timeline {
        position: absolute;
        right: 50px;
        top: 50px;
    }
    .timeline .highlight {
        font-weight:bold;
    }
    blockquote .cite {float:right;}
    .mt-0 { margin-top:0px; }
    img[alt~="center"] {
        display: block;
        margin: 0 auto;
    }
    .callout {
        border-radius: 30px;
        padding: 0 0.5em 0 0.5em;
        width:fit-content;
    }

    .darkened {
        background-color: rgba(0, 0, 0, 0.60);
        color:white;
    }

paginate: true
math: mathjax
---


# Sound Localization Update

<br/>

author: Paolo Marzolo
advisor: Alberto Antonietti
co-adv:  Francesco De Santis

---

# Table of contents
<div class="twocols">
<div>

1. introduction
    - itd/ild/hrtf
1. ear+cochlea 
    - anatomy overview
    - functions
    - bio plausibility
    - DCGC comparison
</div>
<div>

3. MSO and plasticity
    - net overview
    - current issue explanation
    - plastic delays?
    - plastic inhibition?       
4. conclusion
</div>

---
# Today's objectives

<br/>

1. show current state
1. foster discussion on where to go from here
1. practice!

---
## Task definition
<br/>

> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>


![bg left w:550](./img/azim.png)

---
## Why it's interesting
<br/><br/>

1) point-like sensor to spatial
1) localizing is instrumental to selectively improve SNR
1) features special neural features

<!--  independent evolution (Grothe and Pecka, 2014)
    - diets changed to seeds, depriving three ossicles of their function
    * only small, nocturnal mammals survived
    * mother-pup communication calls outside reptilian-bird hearing range -->
---
## Hearing cues

![center w:1150](./img/cues.png)
(Grothe, 2010)

<!-- 
not obvious: you'd think frequency mostly depends on signal
 -->
---
### HRTFs

![bg h:90%](./img/hrtf-cat-azim.png)

<!-- 
the generalization of these cues, which is the sum of all possible aspects that differentiate how the sound arrives to one eardrum from the other, are called the head related transfer functions
-->
---
![bg h:90%](./img/hrtf-elev.png)

---

# Path to auditory nerve
1. Outer ear
2. Middle ear
3. Basilar membrane
4. Inner Hair Cells
5. Active components (Outer Hair Cells)
6. Auditory nerve synapse

<!-- footer: (Meddis and Lopez, 2010) -->

---

<br/>
<br/>
<br/>
<br/>
<br/>
<br/>

![bg w:101%](./img/ear-ext.png)
<!-- 
the external ear has three basic functions:
1. channel sound waves inside the ear canal
2. characterize sound elevation
3. characterize front-back difference

The HRTF will take us from outside the ear up until the eardrum
-->
<div class="callout darkened">

## Outer ear
- accessible!
- HRTFs cover "diffraction, reflection, scattering, 
resonance, and interference phenomena that affect 
the incoming sound before it reaches the eardrum"
</div>

<!-- the alternative would be a very complicated 
physical model.. also very computationally expensive -->

---

## Middle ear
<div class="callout darkened">

- low acoustic impedance of air -> cochlear perilymphatic fluid (4,000 times higher)
- linear system, transfer function is a ratio of pressures depending on freq
* the middle ear does not introduce distortion for sound levels below approximately 130 dB SPL
* modeled by electrical circuits, or mechanical pieces, or digital filter (single or cascade)
* may be resposible for "glide"

</div>

![bg w:101%](./img/ear-mid.png)
<!-- 
the middle ear is characterized by three ossicles...
glide is how the frequency with which a specific point on the BM changes, initially vibrating at a lower frequency, then changing to a higher frequency, when reacting to an impulse such as a click
-->
---
<br/>
<br/>

<center> 

> ### the output signal must be multiplied by an appropriate scalar to achieve a realistic gain
</center>

---
![bg w:100%](./img/ear-coch.png)

---
![bg w:100%](./img/coch-high.png)
<!-- basilar membrane resonates tonotopically -->
---

<!-- footer: "" -->

![bg w:100%](./img/coch-low.png)

<div class="callout darkened">

## Basilar membrane
* asymmetric (the magnitude of the BM response decreases faster for frequencies above the BF than for frequencies below it)
* nonlinear!
* BM responses show more gain at low than at high sound levels
* BF of a cochlear site change depending on level
* also causes suppression and distortion
* responses are fully linear postmortem

</div>

---

## Modelling the BM

![w:90%](./img/gammatone.png)
gammatone filterbank (linear, symmetric frequency response)

---
<!-- footer: https://www.jstage.jst.go.jp/article/ast1980/20/6/20_6_397/_article/-char/en
 -->

# Gammatone issues
<br>

- linear (wrt level)
- symmetric  

![bg right w:90%](./img/gammatone-vs-gammachirp.png )

---
<!-- footer: "(Ruxue Guo et al, 2022)" -->

![bg w:98%](./img/gammachirp-bank.png)

---
<!-- footer: "" -->

### and beyond!

- Tan-Carney model: 
    - level independent chirps
    - gain and bandwidth vary dynamically depending on level
    - accounts for two-tone suppression
- DRNL (Dual Resonance Non Linear):
    - simulates the velocity of vibration of a given site on the BM
    - linear responses at low levels, compressive for moderate levels
    - predicts AN representation of stimuli with complex spectra, used to drive models of brain stem units, and as the basis for a speech processor for cochlear implants

---

#### Inner Hair Cells
![bg w:55%](./img/corti.svg)

<!-- 
vescicle depletion may have a role in adaptation
-->
---
![bg right w:480](./img/ihc-synapse.png)
### from IHC to ANF
- although inner hair cells depolarize, they do not produce an action potential, but a _graded potential_
- to simulate correctly, should distinguish between vesicle *release probability* and vesicle *availability*

<span class="text-small">image from [here](openlearn.open.ac.uk/mod/resource/view.php?id=263162)</span>

---

### Current modeling elements
<br/>
<center>

| feature  | modelling   | 
|:-------------- | --------------:| 
| ln tonotopic organization    | erbspace     |
| approximate frequency    | gammatone     |
| OHC/active hearing    | compression     |
| amplification (gain) | scalar |


---

### Current modeling elements
<br/>
<center>

| feature  | modelling   | 
|:-------------- | --------------:| 
| ln tonotopic organization    | erbspace     |
| ~~approximate frequency~~    | ~~gammatone~~     |
| ~~OHC/active hearing~~    | ~~compression~~     |
| ~~amplification (gain)~~ | ~~scalar~~ |


---
### Future modeling elements?
<br/>
<center>

| feature  | modelling   | 
|:-------------- | --------------:| 
| ln tonotopic organization    | erbspace     |
| - approximate, asymmetric frequency <br> - dynamic, justified gain <br> - active hearing, compression  | gammachirp |

---
#### Existing scheme

![bg w:90%](./img/block-cochlea.png)


---

#### Updated scheme


![bg w:80%](./img/block-cochlea_gammachirp.png)


---

### results:

![bg w:60%](./img/auditory-nerve-fibre-rasterplot.png)

<!-- 
as these are just spikes, spike generators can be initialized in nest to fire accordingly. leaving us with a full-nest network.
-->

---
### results:

![bg h:80%](./img/gammachirp_anf_resopnse.png)

---

![bg left h:70%](./img/gammachirp_anf_resopnse.png)

## The bad part:

- current results with entire net based on long ablation
- gammachirp shows:
    - phase locking
    - more realistic (?) gain
    * less spikes
    * lower engagement of low freq ANFs
    * needs more ablation

---

# MSO and Plasticity

<br>

- so far, we've looked at inputs
- what about the rest of the network?
- net overview
- current issue explanation
- plastic delays?
- plastic inhibition?

---

## First net

![bg w:58%](./img/net_struct.png)

---

## Updated design
&nbsp; &nbsp; &nbsp; &nbsp; ![w:1000](./img/netvis.png)

---

## Differences

<div class="twocols mt-0">
<div class="mt-0">

![left w:500](./img/net_struct.png)
</div>
<div class="mt-0">
<br>

![right w:600](./img/netvis.png)


</div>
</div>

---


![bg left w:600](./img/net_struct.png)

### Changes


- Design-wise:
    - Updated weights
    - Included LNTB for inh
    - Updated delays (we'll see effect later)
- Technical:
    - Batch processing
    - Cache on disk
    - Batched results

---

![bg left w:100%](./img/example_full_single_input.png)

## sidenote: results
### what we look for:
- LSO ipsi, MSO contra
- MSO preferring specific angles, different from zero
- MSO good for low freqs
- LSO crossing around zero
- HRTF results

---


![bg w:98%](./img/example_good_result.png)


---

## What's behind the MSO?
<br>

- to process ITDs, you need single-spike sensitivity
- inhibition is clearly very important:
    - calyx of Held
    - bilateral inhibition
    - phase locked
- the answer must be with inhibition (*)

---

### MSO structure
- bipolar
- bilateral inputs
- 2 inh, 2 exc 


![w:1200](./img/myoga/mso_shape.png)


---

![bg right w:102%](./img/myoga/single_start.png)

### Start easy: two inputs

<br>

- peak voltage time is shifted
- shift possible in both directions
- synaptic weight matters... a bit

---
### Zoomed

![bg h:95%](./img/myoga/single_zoomed.png)


---

<div class="twocols mt-0">
<div class="mt-0">

##### Peak delay

![left w:540](./img/myoga/single_delayed.png)
</div>
<div class="mt-0">

##### Peak advance

![left w:540](./img/myoga/single_advanced.png)
</div>
</div>

---

![bg right w:102%](./img/myoga/triple_start.png)


### Three inputs

<br>
<br>

- modulating only contra IPSP
- best ITD both delayed and advanced

---

<div class="twocols mt-0">
<div class="mt-0">

![left w:550](./img/myoga/triple_-1_left.png)
</div>
<div class="mt-0">

![left w:550](./img/myoga/triple_-1_right.png)
</div>
</div>

<!-- 
with a delay of -1, the neuron only spikes for left sounds
 -->

---


<div class="twocols mt-0">
<div class="mt-0">

![left w:550](./img/myoga/triple_.1_left.png)
</div>
<div class="mt-0">

![left w:550](./img/myoga/triple_.1_right.png)
</div>
</div>

<!--  
with a delay of 0.1, the neuron only spikes for right sounds -->

---

#### In the same plot

![bg h:90%](./img/myoga/triple_myoga_best.png)

---
#### Replicated (desa!)

![w:1100](./img/myoga/triple_desa.png)

---

### Four inputs

![bg right w:102%](./img/myoga/quad_my.png)

<br>
<br>

- similar results to three inputs: if you change one keeping the other stable you get a similar curve
- this means an extra knob to turn
- still needs timing plasticity

<!-- 
myoga results is pretty much identical to the three inputs one
-->

---
#### Desa result

![bg w:90%](./img/myoga/quad_desa.png)

---

![bg w:90%](./img/myoga/quad_desa_best_itd.png)

---

![bg w:90%](./img/effect_deltat.png)

<div style="position:absolute; bottom: 2em; left:25em">

### Changing delays

</div>

---

# Issues

* bio plausibility:
    - how exactly do these timings change?
    - limited evidence on plasticity of timing
* technical:
    - angle error is a one-dimensional measure
    - differences in arrival time of bilateral inhibition are two dimensions
    - what to do?