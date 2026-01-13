# Contributing to DERP (Discovering Elusive Recordings Project)

Thank you for your interest in contributing to the Cojumpendium Lost Media Scraper! This project is a community effort to archive and preserve lost media from Cojum Dip (2004-2011).

## How to Contribute

### For Cojumpendium Research Group Members

#### 1. Adding Search Terms
If you know of additional terms, names, or venues that should be searched:

1. Edit `config.yaml`
2. Add your terms to the appropriate section:
   ```yaml
   search:
     terms:
       - "Your New Search Term"
   ```
3. Test the changes:
   ```bash
   python -m cojumpendium_scraper scrape --dry-run
   ```

#### 2. Sharing Findings
When you discover lost media:

1. Run the export command:
   ```bash
   python -m cojumpendium_scraper export
   ```
2. Review the exported data in the `exports/` directory
3. Share your findings with the group
4. Update the database with notes on important discoveries

#### 3. Improving Platform Scrapers
If you have expertise with specific platforms:

1. Look at the relevant scraper in `cojumpendium_scraper/scrapers/`
2. Enhance the search or extraction logic
3. Test your changes thoroughly
4. Submit a pull request

#### 4. Adding New Platforms
To add support for a new platform:

1. Create a new scraper file: `cojumpendium_scraper/scrapers/newplatform.py`
2. Inherit from `BaseScraper`
3. Implement `search()` and `scrape_url()` methods
4. Add the platform to `cli.py`
5. Test thoroughly

Example:
```python
from .base import BaseScraper

class NewPlatformScraper(BaseScraper):
    async def search(self, search_terms, **kwargs):
        # Implement search logic
        pass
    
    async def scrape_url(self, url, **kwargs):
        # Implement scraping logic
        pass
```

### For Developers

#### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/derp.git
   cd derp
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8  # Optional dev tools
   ```
4. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and modular

#### Testing

Before submitting changes:

1. Test the CLI commands:
   ```bash
   python -m cojumpendium_scraper init
   python -m cojumpendium_scraper scrape --dry-run
   python -m cojumpendium_scraper stats
   python -m cojumpendium_scraper export
   ```

2. Verify no syntax errors:
   ```bash
   python -m py_compile cojumpendium_scraper/**/*.py
   ```

3. Test with different configurations

#### Submitting Changes

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request with:
   - Clear description of changes
   - Why the changes are needed
   - Any testing you've done

## Areas for Contribution

### High Priority
- [ ] Enhance Wayback Machine scraper with better filtering
- [ ] Improve MySpace music player extraction
- [ ] Add support for more archive services
- [ ] Implement better duplicate detection
- [ ] Add automated testing

### Medium Priority
- [ ] Enhance media extractors for better format support
- [ ] Add support for more social media platforms
- [ ] Improve error handling and recovery
- [ ] Add progress persistence for interrupted scrapes
- [ ] Better logging and debugging tools

### Low Priority
- [ ] Web interface for browsing discoveries
- [ ] Automated categorization of findings
- [ ] Integration with other archival tools
- [ ] Performance optimizations
- [ ] Multi-language support

## Platform-Specific Contributions

### Wayback Machine
- Improve CDX API query optimization
- Handle edge cases in timestamp parsing
- Better rate limit management

### MySpace
- Enhanced music player link extraction
- Photo album scraping
- Comments and friend list extraction

### YouTube
- Video metadata extraction
- Comment scraping
- Channel information

### Audio/Video Extraction
- Support for more formats
- Better quality detection
- Metadata preservation

## Reporting Issues

If you find bugs or have suggestions:

1. Check if the issue already exists
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version)
   - Relevant logs or error messages

## Code Review Process

All contributions will be reviewed for:
- Code quality and style
- Functionality and correctness
- Performance impact
- Documentation completeness
- Test coverage

## Getting Help

- Check the README.md and QUICKSTART.md first
- Review existing issues and pull requests
- Ask questions in discussions or issues
- Contact the Cojumpendium research group

## Recognition

Contributors will be acknowledged in:
- Project README
- Release notes
- Special thanks from the band and Cojumpendium group

## Important Notes

### Legal and Ethical
- Respect rate limits and robots.txt
- Only scrape publicly available content
- This is for archival and historical purposes
- We have explicit permission from the band

### Data Privacy
- Don't commit sensitive information
- Keep API keys and credentials out of code
- Use environment variables or config files
- Don't share personal data of community members

### Quality Standards
- Write clean, documented code
- Test your changes thoroughly
- Follow the existing code structure
- Ask for help if you're unsure

## Community Guidelines

- Be respectful and constructive
- Help other contributors
- Share knowledge and discoveries
- Credit others' work appropriately
- Focus on the goal: preserving Cojum Dip history

## Thank You!

Every contribution helps preserve an important piece of music history. Whether you're adding a search term, improving code, or sharing a discovery, you're making a difference!

---

**Remember**: We're not just scraping data – we're preserving art and culture. Handle everything with care and respect for the artists and community involved.
