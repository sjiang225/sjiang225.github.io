# Siqi Jiang Personal Website

This repository hosts Siqi Jiang's academic homepage at <https://sjiang225.github.io/>.

The site is built with Jekyll and GitHub Pages. It highlights research interests, selected publications and preprints, education, and academic service.

## Local Development

Install the GitHub Pages dependencies, then run the local server:

```bash
bundle install
bundle exec jekyll serve
```

The site will be available at <http://127.0.0.1:4000/>.

## Main Content Files

- `_pages/about.md`: homepage content
- `_config.yml`: site metadata and author profile
- `_data/navigation.yml`: top navigation
- `assets/css/main.scss`: custom styling

## Citation Data

The Google Scholar citation refresh workflow is configured in `.github/workflows/google_scholar_crawler.yaml`.
To enable it, add a repository secret named `GOOGLE_SCHOLAR_ID` with the Scholar profile ID.
