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
paginate: true
math: mathjax
---
<div class='timeline'>intro-anato-<span class='highlight'>simul:IHC</span>-conclu
</div>


# Sound Localization Basics
auth: Paolo Marzolo
adv:  Francesco De Santis

---
# Table of contents
<div class="twocols">
<div>

1. introduction
    - task definition
    - why it's interesting
    - basic concepts
1. anatomical 
    - overall structure
    - my part
</div>
<div>

3. simulation
    - nest and architecture
    - brian2-brian2hears
    - my implementation and workflow
4. conclusion
</div>

---
# Introduction
- double presentation
- objectives:
    - familiarize audience with the subjects
    - present what i've been working on
    - get some more presentation practice
- feedback welcome!

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>

<div class="twocols mt-0">
<div>


### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
</div>


---

![bg left w:600](./img/azim.png)

> a subject might call out the coordinates "minus 45, 30," indicating that the sound came from 45° to the left of the subject and from 30° above the horizontal plane.
\
(Wightman and Kistler, 1992)

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>

<div class="twocols mt-0">
<div>

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
<p class="break"></p>

</div>

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>
<div class="twocols mt-0">
<div>

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
- God's eye <span class='text-small'>(Gilkey et al., 1995)</span>
</div>
</div>

---
![center w:780](./img/god-eye.png)

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>

<div class="twocols mt-0">
<div>

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
- God's eye <span class='text-small'>(Gilkey et al., 1995)</span>
</div>
<div>

### other mammals
- mostly MAA:
    - 2AFC
</div>
</div>

---
![center w:570](./img/gerbil-2c.png)
(Tolnai et al., 2017) - virtual headphones

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>

<div class="twocols mt-0">
<div>

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
- God's eye <span class='text-small'>(Gilkey et al., 1995)</span>
</div>
<div>

### other mammals
- mostly MAA:
    - 2AFC
- 6 AFC alternative for SNR
</div>
</div>

---
![center w:580](./img/gerbil-6c.png)
(Lingner et al., 2012) - sound localization SNR

---
## why it's interesting
<br/><br/>

1. point-like sensor to spatial
1. limited cues are enough to accomplish it
1. evolutionary perspective

---
## why it's interesting
1. point-like sensor to spatial -> consider vision and somatosensation
1. limited cues are enough to accomplish it
1. evolutionary perspective
---

## why it's interesting

1. point-like sensor to spatial -> consider vision and somatosensation
1. ### limited cues are enough to accomplish it
    - 3 classes of cues: ITD, ILD, spectral

---
<br/>

![center w:1150](./img/cues.png)
(Grothe and Pecka, 2014)

---
## why it's interesting

1. point-like sensor to spatial -> consider vision and somatosensation
1. ### limited cues are enough to accomplish it
    - 3 classes of cues
    * spectral cues don't change in horizontal -> binaural
    * small ranges: ITD $\in [\pm 0.6 \micro s ]$, ILD $\in [\pm 50dB ]$
    * ITD viable in larger heads, ILD frequency dependent
        - ILD high freq affected most (Rayleigh, 1875)
        - for humans, viable >1.3 kHz 

---
TODO: HRTF!

---

## why it's interesting

1. point-like sensor to spatial -> consider vision and somatosensation
1. limited cues are enough to accomplish it
3. ### evolutionary perspective
    * independent evolution (Grothe and Pecka, 2014)

---
![bg w:80%](./img/ear-evol.png)
<!-- 
common evolutionary pressure is unclear for now
this also means possibly independent solutions! -->

---

## why it's interesting

1. point-like sensor to spatial -> consider vision and somatosensation
1. limited cues are enough to accomplish it
1. ### evolutionary perspective
    - independent evolution (Grothe and Pecka, 2014)
    - diets changed to seeds, depriving three ossicles of their function
    * only small, nocturnal mammals survived
    * mother-pup communication calls outside reptilian-bird hearing range

---

## basic concepts: review
<br/>

1) ILD, ITD, spectral cues
1) HRTFs contain all of them
1) specialized anatomical and physiological properties not found anywhere else
1) parallel evolution means different mechanisms may be in use in different _classes_

---
# anatomy of hearing

![bg right w:489](./img/audio-pathway.png)


- auditory pathway overview
- desa working on anf to midbrain
- i decided to start with the inputs, so cochlea simulation
- stills taken from [CrashCourse](https://www.youtube.com/@crashcourse) and [wikipedia](https://en.wikipedia.org/wiki/Hair_cell)

---

![bg w:100%](./img/ear-ext.png)
<!-- 
formed of three parts...
here's my opinion on the external ear, for our purposes.
the external ear has three basic functions:
1. channel sound waves inside the ear canal
2. characterize sound elevation
3. characterize front-back difference
-->
---

![bg w:100%](./img/ear-mid.png)
<!-- 
the middle ear is characterized by three ossicles...
it is also, interestingly, a closed chamber, can be opened by swallowing, blowing into your nose, chewing. an example is if you've ever been diving
we've seen the three ossicles before!
the stapes "knocks" on the oval window, against the labyrinth.
the amplification given by the ossicles is necessary because moving a sound through liquid, like in the labyrinth, is harder than through air.
-->
---
![bg](./img/ear-lab.png)

---
![bg w:100%](./img/ear-coch.png)

---
![bg w:100%](./img/corti.png)
<!-- basilar membrane -->
---
![bg w:100%](./img/coch-high.png)
<!-- basilar membrane resonates tonotopically -->
---
![bg w:100%](./img/coch-low.png)

---

![bg w:65%](./img/cochlea-crosssection.svg)
<!-- here's another image, from the side -->
---
![bg w:105%](./img/cochlea-crosssection.svg)

<!-- you'll notice that there are two types of hair cells, outer hair cells and inner hair cells -->
---
![bg fit](./img/corti.svg)

<!-- 
inner hair cells are very innervated, about 10 cochlear nerve fibers per hair cell, while outer hair cells are much less innervated, as one cochlear nerve fiber innervates multiple of them.
outer hair cells actually have a very specific function: they non-linearly compress the audible range about a million to a hundred
-->

---
![center](./img/ear-active-process.png)
<!-- the threshold is 0.1nm -> 0dB; loudest is 10nm -> 120dB -->

---
![bg left w:600](./img/ihc-stim.png)
Sensory epithelium of the chicken cochlea:
- hexagonal array of short hair cells bordered supporting cells
- deflecting causes depolarization

(Hudspeth, 2008)

<!-- TODO mention phase locking as ihc move back and forth between hyper pol and depol -->

--- 
![bg left w:600](./img/ihc-just-d.png)
1. Deflection of the bundle bends the stereociliary pivots, tenses the tip link, and opens the transduction channel
2. $K^+$ and $Ca^{2+}$ enter the cytoplasm and depolarize the hair cell
3. $Ca^{2+}$ interacts with a molecular motor and slips down, lowering tension

(Hudspeth, 2008)

---
![bg right w:480](./img/ihc-synapse.png)
- although inner hair cells depolarize, they do not produce an action potential, but a _graded potential_
- the depolarization causes release of glutamate in ribbon synapse
- glutamate stimulates action potential in type I fibers

---
<div class="twocols mt-0">
<div class="mt-0">

![left w:450](./img/after-anf.png)
</div>
<div class="mt-0">

![right w:430](./img/mso-lso.png)

</div>
</div>
<!-- 
which then connect to a variety of different cell types and go on to reach the superior olivary complex, which is outside of our scope -->

---
# what are we doing? what am i doing?
- what is our role? validating a model


---

# simulation

3. simulation
    - nest and architecture
    - brian2-brian2hears
    - my implementation and workflow
4. conclusion
5. feature steps

---

# how do we code this?


---


<!-- _class: -->