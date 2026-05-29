---
permalink: /
title: "Siqi Jiang"
excerpt: "Ph.D. candidate at NJIT | Foundation Models | Graph Learning | AI for Biomedical and Financial Forecasting"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

{% if site.google_scholar_stats_use_cdn %}
{% assign gsDataBaseUrl = "https://cdn.jsdelivr.net/gh/" | append: site.repository | append: "@" %}
{% else %}
{% assign gsDataBaseUrl = "https://raw.githubusercontent.com/" | append: site.repository | append: "/" %}
{% endif %}
{% assign url = gsDataBaseUrl | append: "google-scholar-stats/gs_data_shieldsio.json" %}

<span class='anchor' id='about-me'></span>
# About Me

I’m a Ph.D. candidate in the Department of Computer Science at the New Jersey Institute of Technology (NJIT), advised by [**Prof. Zhi Wei**](https://web.njit.edu/~zhiwei/) and [**Prof. Dantong Yu**](https://sites.google.com/site/dantongyu/home). My research centers on large language models (LLMs), foundation models, graph-based learning, and time-series analysis, with applications in financial forecasting, biomedical modeling, and scientific discovery. I am particularly interested in building scalable, interpretable AI systems that perform reliably in high-stakes, real-world scenarios.

Prior to NJIT, I earned my M.Sc. in Business Intelligence & Analytics from Stevens Institute of Technology and received dual bachelor’s degrees in Electrical Engineering and Finance from Shanghai Normal University and East China University of Science and Technology.

<span class='anchor' id='news'></span>
# News
- *Mar 2026*: Our work on feature selection with unsupervised deep embedding for single-cell RNA-seq clustering was published in *Briefings in Bioinformatics*.
- *Mar 2026*: We updated GeneMamba, a foundation model for single-cell transcriptomics, on arXiv.
- *Feb 2026*: Our survey on AI agents for biological research was published in *Briefings in Bioinformatics*.
- *Dec 2025*: ESPNet appeared at IEEE Big Data.
- *Nov 2024*: MultiSC was published in *Briefings in Bioinformatics*.
- *Nov 2023*: Our dynamic heterogeneous graph neural network for mutual fund performance estimation appeared at ACM ICAIF.

<span class='anchor' id='research'></span>
# Research Interests
- Foundation models and agentic AI for biomedical discovery
- Graph neural networks and interpretable representation learning
- Time-series modeling and financial forecasting
- Multi-omics and single-cell data analysis

<span class='anchor' id='-publications'></span>
# Selected Publications & Preprints

<div class="pub-list">
  <article class="pub-item">
    <div class="pub-meta">
      <span class="pub-badge">BIB 2026</span>
    </div>
    <div class="pub-body">
      <h3>Integrating feature selection with unsupervised deep embedding for clustering single-cell RNA-seq data</h3>
      <p class="pub-authors">Cheng Zhong, <strong>Siqi Jiang</strong>, Zhi Wei.</p>
      <p class="pub-venue"><em>Briefings in Bioinformatics</em>, 27(2), bbag082, 2026.</p>
      <p class="pub-note">A joint feature selection and clustering framework for scRNA-seq analysis that improves interpretability through compact, biologically meaningful gene panels.</p>
      <p class="pub-links"><a href="https://doi.org/10.1093/bib/bbag082">Paper</a></p>
    </div>
  </article>

  <article class="pub-item">
    <div class="pub-meta">
      <span class="pub-badge">BIB 2026</span>
    </div>
    <div class="pub-body">
      <h3>Artificial Intelligence agents for biological research: a survey</h3>
      <p class="pub-authors">Cong Qi, Wenbo Wang, <strong>Siqi Jiang</strong>, Qin Liu, Xun Song, Hanzhang Fang, Zhi Wei.</p>
      <p class="pub-venue"><em>Briefings in Bioinformatics</em>, 27(1), bbag075, 2026.</p>
      <p class="pub-note">A systematic survey of agentic AI for biological research, covering reasoning, planning, tool use, evaluation, and resource integration.</p>
      <p class="pub-links"><a href="https://doi.org/10.1093/bib/bbag075">Paper</a> <a href="https://github.com/MineSelf2016/biological_agents_survey">Resource</a></p>
    </div>
  </article>

  <article class="pub-item">
    <div class="pub-meta">
      <span class="pub-badge">arXiv 2025</span>
    </div>
    <div class="pub-body">
      <h3>GeneMamba: An Efficient and Effective Foundation Model on Single Cell Data</h3>
      <p class="pub-authors">Cong Qi, Hanzhang Fang, <strong>Siqi Jiang</strong>, Xun Song, Tianxing Hu, Wei Zhi.</p>
      <p class="pub-venue">arXiv:2504.16956, 2025.</p>
      <p class="pub-note">A scalable single-cell foundation model based on bidirectional state-space modeling and biologically informed objectives.</p>
      <p class="pub-links"><a href="https://arxiv.org/abs/2504.16956">arXiv</a></p>
    </div>
  </article>

  <article class="pub-item">
    <div class="pub-meta">
      <span class="pub-badge">IEEE Big Data 2025</span>
    </div>
    <div class="pub-body">
      <h3>ESPNet: Edge-Aware Graph Representation Learning Over Analyst-Firm Bipartite Networks for Earnings Surprise Prediction</h3>
      <p class="pub-authors"><strong>Siqi Jiang</strong>, Xinyuan Tao, Ajim Uddin, Zhi Wei, Dantong Yu.</p>
      <p class="pub-venue"><em>2025 IEEE International Conference on Big Data</em>, pp. 985-994, 2025.</p>
      <p class="pub-note">A financial graph learning framework that models analyst-firm interactions as an edge-aware bipartite network for earnings surprise prediction.</p>
      <p class="pub-links"><a href="https://ieeexplore.ieee.org/abstract/document/11402270">Paper</a></p>
    </div>
  </article>

  <article class="pub-item">
    <div class="pub-meta">
      <span class="pub-badge">BIB 2024</span>
    </div>
    <div class="pub-body">
      <h3>MultiSC: A Deep Learning Pipeline for Analyzing Multiomics Single-Cell Data</h3>
      <p class="pub-authors">Xiang Lin<sup>*</sup>, <strong>Siqi Jiang</strong><sup>*</sup>, Le Gao<sup>*</sup>, Zhi Wei, Junwen Wang.</p>
      <p class="pub-venue"><em>Briefings in Bioinformatics</em>, 25(6), bbae492, 2024.</p>
      <p class="pub-note">A multi-omics single-cell analysis pipeline for integrating gene expression, chromatin accessibility, and transcription factor protein expression.</p>
      <p class="pub-links"><a href="https://doi.org/10.1093/bib/bbae492">Paper</a> <a href="https://github.com/xianglin226/Multi-SC">Code</a></p>
    </div>
  </article>

  <article class="pub-item">
    <div class="pub-meta">
      <span class="pub-badge">ICAIF 2023</span>
    </div>
    <div class="pub-body">
      <h3>The Network of Mutual Funds: A Dynamic Heterogeneous Graph Neural Network for Estimating Mutual Funds Performance</h3>
      <p class="pub-authors"><strong>Siqi Jiang</strong>, Ajim Uddin, Zhi Wei, Dantong Yu.</p>
      <p class="pub-venue"><em>The 4th ACM International Conference on AI in Finance</em>, 2023.</p>
      <p class="pub-note">A dynamic heterogeneous graph neural network for modeling relationships among funds, assets, advisors, firms, and managers.</p>
      <p class="pub-links"><a href="https://doi.org/10.1145/3604237.3626910">Paper</a></p>
    </div>
  </article>
</div>

<span class='anchor' id='education'></span>
# Education
- *2021.09 - Present*, New Jersey Institute of Technology, Ph.D. in Computer Science
- *2019.09 - 2021.06*, Stevens Institute of Technology, M.Sc. in Business Intelligence & Analytics
- *2015.09 - 2019.06*, Shanghai Normal University, B.Eng. in Electric Engineering & Automation

<span class='anchor' id='service'></span>
# Academic Service
- *Conference reviewing*: IEEE International Conference on Big Data, ACM International Conference on AI in Finance, IEEE International Conference on Systems, Man, and Cybernetics, Wireless and Optical Communications Conference
- *Journal reviewing*: Briefings in Bioinformatics, IEEE Internet of Things Journal

