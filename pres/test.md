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
    div.twocols { margin-top: 10px; column-count: 2;}
    div.twocols p:first-child,
    div.twocols h1:first-child,
    div.twocols h2:first-child,
    div.twocols ul:first-child,
    div.twocols ul li:first-child,
    div.twocols ul li p:first-child {
        margin-top: 0 !important;
    }
    div.twocols p.break {
        break-before: column;
        margin-top: 0;
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

1. introduction
    - task definition
    - why it's interesting
    - basic concepts
1. anatomical 
    - overall structure
    - my part

<p class="break"></p>

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

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
<p class="break"></p>


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

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
<p class="break"></p>

</div>

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>
<div class="twocols mt-0">

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
- God's eye <span class='text-small'>(Gilkey et al., 1995)</span>
<p class="break"></p></div>

---
![center w:780](./img/god-eye.png)

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>

<div class="twocols mt-0">

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
- God's eye <span class='text-small'>(Gilkey et al., 1995)</span>
<p class="break"></p>

### other mammals
- mostly MAA:
    - 2AFC
</div>

---
![center w:570](./img/gerbil-2c.png)
(Tolnai et al., 2017) - virtual headphones

---
## Task definition
> The ability to identify the location of a sound source in a sound field. <span class='cite text-small'>(Jutras et al., 2020)</span>

<div class="twocols mt-0">

### humans
- report verbally <span class='text-small'>(Wightman and Kistler, 1992)</span>
- nose pointing <span class='text-small'>(Makous and Middlebrooks, 1990)</span>
- God's eye <span class='text-small'>(Gilkey et al., 1995)</span>
<p class="break"></p>

### other mammals
- mostly MAA:
    - 2AFC
- 6 AFC alternative for SNR
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
<!-- this also means possibly independent solutions! -->

---

<!-- ## why it's interesting

1. point-like sensor to spatial -> consider vision and somatosensation
1. limited cues are enough to accomplish it
3. ### evolutionary perspective
    - independent evolution (Grothe and Pecka, 2014)
    - diets changed to seeds, depriving three ossicles of their function
    * only small, nocturnal mammals survived
    * mother-pup communication calls outside reptilian-bird hearing range

---

1. anatomical 
    - overall structure
    - my part

<p class="break"></p>

3. simulation
    - nest and architecture
    - brian2-brian2hears
    - my implementation and workflow
4. conclusion -->

---
# what are we doing? what am i doing?
- what is our role? validating a model
- 
---

# how do we code this?


---


<!-- _class: -->