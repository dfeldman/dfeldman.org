---
title: "KubeCon Content Browser"
date: 2024-11-16T00:35:36-05:00
# TURN THIS OFF TO PUBLISH
draft: false
# Whether to show on the home view (highlights) or not
showInHomeView: true
#linkTo: "https://dfeldman.org/labs/kubecon_browser/kcna2024/"
---
## KubeCon Content Browser
I got fed up with endlessly sifting through KubeCon talks and presentations to find that one gem. You know, the talk where you vaguely remember the topic but forgot the speaker, or vice versa? Instead of just griping, I decided to fix it: I made the KubeCon Content Browser. It’s a nifty tool that pulls videos and slides together, lets you search talks by topic, and even adds AI-generated descriptions and notes. Basically, I wanted to be able to quickly browse and search the contents of the whole conference.

It’s got some rough edges—mobile experience isn’t great yet, and a few presentations are still MIA—but even as it stands, it’s an awesome way to dive into KubeCon content without losing your sanity.

{{< raw-html >}}
<center><img src="https://webassets.dfeldman.org/labs/kubecon_browser/kcna2024/screenshots/kubecon-browser-1.png" alt="Screenshot" width="60%" align="center"></center>
{{</ raw-html >}}
## Try it [Here](https://dfeldman.org/labs/kubecon_browser/kcna2024/#1howe). 

## What Makes It Cool
1. Dual View: Watch the talk video and scroll through the slides side-by-side, if your screen is big enough.
1. Searchable Everything: Quickly find presentations using keywords, tags, or AI-generated summaries.
1. AI Additions: Automated descriptions, outlines, and even related talks (this part needs work).

## How it works
All the data is in .json files, and processed and searched on the client side. There is no backend. This is a bit more demanding on the browser, but means I don't have to set up a server!

1. Gathered all the KubeCon schedule HTML files, then parsed them to grab content URLs.
1. Downloaded all the URLs from the YouTube playlist using JS.
1. Matched YouTube videos to presentations with some hacky magic.
1. Pulled YouTube transcripts for talks and fed them into GPT-4o to summarize and tag.
1. Converted slides into PNGs for browser compatibility (turns out mobile browsers hate PDFs).
1. Hosted the JSON files and slides on GitHub Pages + CloudFront.

All of this is in a series of pretty hacky scripts.

## Copyright?
All the data displayed is copyrighted by CNCF and its original owners. I'm just trying to make it easier to search and browse. Every session has a link to the original contents on Sched, YouTube, and slides download.

## How I made it
I'm proud to say I got the first version of this working the same day KubeCon ended!

After that, I added the AI features, slide previews, and greatly improved UI over several more days. 

I'm not a web developer. I relied heavily on Claude and ChatGPT to learn what I needed to. 

## What's next?
I've got a long to-do list on this project! Since it's just a side quest, I'm not sure how much more I'll be able to do. 

I'd like to have a statically-rendered HTML version as well. The JS UI isn't for everyone. 

Right now, it doesn't include every talk - just the ones that I had complete data for on Friday (the day KubeCon ended). It would be nice to have some info for the incomplete sessions, and also I'm sure the KubeCon team has uploaded a lot more data. 

It did mangle a few people's names in the titles. I'm not certain why. This is a priority to fix, but it's time-consuming.

Finally, it would be fun to do this for many other conferences! I've already had a request to do it for GopherCon. Perhaps I could make this a repeatable service instead of just scratching my own itch!