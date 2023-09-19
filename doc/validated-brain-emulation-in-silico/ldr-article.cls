% This is the LaTex style file for the Journal "Language Development Research"
% version: 1.1 (2023)
% Author: Mitja Nikolaus (mitja.nikolaus@posteo.de)
% The repository for the source files can be found at
%
%     https://github.com/mitjanikolaus/ldr-template
%

\ProcessOptions

% Load LaTeX's article class 
\LoadClass[a4paper,12pt,notitlepage]{article}

% Support for floating figures and tables
\usepackage{graphicx}

% Support for different font colors
\usepackage{xcolor}

% Allow use of SplitList for \orcids command
\usepackage{xparse}

% Redefine the page margins
\RequirePackage[left=2.5cm,right=2.5cm,bottom=4cm,top=1.5cm,headsep=2.5cm,includehead]{geometry}

% Define the fonts
\RequirePackage[default]{sourcesanspro}
\RequirePackage[default,regular]{sourceserifpro}
\usepackage[T1]{fontenc}

% Title page font
\newcommand{\titlepagefontsize}{\fontsize{10}{12}\selectfont}
\newcommand{\titlefont}{\fontfamily{SourceSansPro-LF}\bfseries\fontsize{16}{18}\selectfont}

% Text font size and family
\AtBeginDocument{%
\apptocmd{\normalsize}{\fontsize{12}{14}\selectfont}{}{}%
\apptocmd{\normalfont}{\fontfamily{SourceSerifPro-LF}\selectfont}{}{}
}

% Sans serif font family
\newcommand{\normalsansfont}{\fontfamily{SourceSansPro-LF}\selectfont}

% Define page header and footer
\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\titlepagefontsize\textit{(journal tbd)}}
\fancyhead[R]{\titlepagefontsize \thepage}
\renewcommand{\headrulewidth}{0pt}
% Define the same header and footer for title page
\fancypagestyle{plain}{%
}

% Set title and authors' font by redefining the maketitle command
\makeatletter
\def\@maketitle{%
  \newpage
  \null
  \vskip 2em%
  \begin{center}%
  \let \footnote \thanks
    {\titlefont \@title \par}%
    \vskip 1.5em%
    {\titlepagefontsize
      \lineskip .5em%
      \begin{tabular}[t]{c}%
        \@author
      \end{tabular}\par}%
    % Do not print date on title page
    %\vskip 1em%
    %{\large \@date}%
  \end{center}%
  \par
  \vskip 1.5em}
\makeatother

%Put abstract header on same line as abstract, define font size
\renewenvironment{abstract}%
		 {%
		  \begin{list}{}%
		     {\setlength{\rightmargin}{0cm}%
		      \setlength{\leftmargin}{0cm}}%
		   \item[]\ignorespaces%
		   \titlepagefontsize
		   \textbf{Abstract:}}%
		 {\unskip\end{list}}

% Define additional title page commands
\newcommand{\keywords}[1]{\titlepagefontsize\textbf{Keywords: }#1\\[\baselineskip]}

\newcommand{\correspondingauthor}[1]{\titlepagefontsize\textbf{Corresponding author: }#1 \\[\baselineskip]}

% for a single ORCID
\newcommand{\orcid}[1]{\titlepagefontsize\textbf{ORCID ID: }\url{#1} \\[\baselineskip]}

% for a multiple ORCIDs delimited by semicolon ;
\newcommand{\orcids}[1]{\titlepagefontsize\textbf{ORCID IDs: }\orcidlist{#1} \\[\baselineskip]}
\NewDocumentCommand{\orcidlist}{ >{\SplitList{;}} m }{%
  \ProcessList{#1}{\orciditem}%
  \firstitemtrue
}

% Add semicolons before each new item except the first one
\newif\iffirstitem
\firstitemtrue
\newcommand\orciditem[1]{%
  \iffirstitem
    \firstitemfalse
  \else
    ; %
  \fi
  \url{#1}
}

\newcommand{\citationinfo}[1]{\titlepagefontsize\textbf{Citation: }#1 \\[\baselineskip]%
% The end of title page is after the end of the citation info. We add a page break and return to the normal font size
\clearpage\normalsize}


% Define section header layouts
\RequirePackage{titlesec}
\titleformat{\section}
  {\centering\bfseries}
  {\thesection}{1em}{}
\titleformat{\subsection}
  {\bfseries}
  {\thesection}{1em}{}
\titleformat{\subsubsection}
  {\bfseries\itshape}
  {\thesection}{1em}{}
\titleformat{\paragraph}[runin]
{\bfseries}
{\thesection}{1em}{}[.]
\titlespacing*{\paragraph}{1.5em}{0em}{\wordsep}
\titleformat{\subparagraph}[runin]
{\bfseries\itshape}
{\thesection}{1em}{}[.]
\titlespacing*{\subparagraph}{1.5em}{0em}{\wordsep}

% Remove the numbers from all the headings (\section, \subsection, etc.)
\setcounter{secnumdepth}{-1}

% Do not indent paragraphs, but add a new line
\usepackage[parfill,skip=\baselineskip]{parskip}


% Define figure and table caption styles
\usepackage{caption}
\DeclareCaptionFont{captionfont}{\normalfont}
\captionsetup[figure]{singlelinecheck=off, margin={5pt,0pt}, textfont={it,bf},labelfont={bf},labelsep=period,font=captionfont}
\captionsetup[table]{singlelinecheck=off, margin={5pt,0pt}, textfont={it,bf},labelfont={bf},labelsep=period,font=captionfont}


\renewcommand{\figurename}{Figure}

% Use biblatex for reference management
\RequirePackage[style=apa]{biblatex}
% References section is only left-justified
\renewcommand*{\bibfont}{\raggedright}
% Add new lines between bib entries instead of indented paragraphs
\renewcommand*{\bibparsep}{\baselineskip}
\renewcommand*{\bibhang}{0em}


% Remove ugly colorful boxes around references (and make URLs blue)
\definecolor{darkblue}{RGB}{5, 99, 193}
\usepackage[colorlinks,linkcolor=.,citecolor=.,urlcolor=darkblue]{hyperref}

% Allow line breaks in long URLs
\usepackage[nobiblatex]{xurl}

% Improve alignment of justifified text
\usepackage{microtype}
