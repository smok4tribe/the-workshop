# The Workshop

The Workshop is a local-first Deck Engineering Platform for Commander.

It is not a generic deck builder.
It is a structured workspace for deck analysis, recommendations, decisions, versions, and reports.

## Sprint 1

Sprint 1 proves the core engineering loop locally:

Project -> Brief -> Deck Import -> DeckVersion -> Card Facts -> Basic Knowledge -> Analysis -> Weakness -> Recommendation -> Decision -> New DeckVersion -> Report

## Repository Layout

- `/docs` contains product, architecture, RFC, ADR, and planning documentation.
- `/workshop` contains the executable local prototype files.

## Storage Model

- JSON stores structured data.
- Markdown stores readable reports and notes.

This repository intentionally starts local-first. It is not a full web application yet.
