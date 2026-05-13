import asyncio
import logging
from urllib.parse import quote_plus
from aegis.tools.base import BaseTool

logger = logging.getLogger(__name__)

class OpenURLTool(BaseTool):
    name = "open_url"
    description = "Open a URL in the browser using Playwright."

    async def run(self, url: str, page=None, **kwargs) -> str:
        self.log_action(url=url)
        if not page:
            return "Error: Browser page not initialized."
        try:
            await page.goto(url, wait_until="networkidle")
            return f"Successfully opened: {url}"
        except Exception as e:
            return f"Failed to open URL {url}: {str(e)}"


class SearchWebTool(BaseTool):
    name = "search_web"
    description = "Open a web search results page for a query."

    async def run(self, query: str, page=None, **kwargs) -> str:
        self.log_action(query=query)
        if not page:
            return "Error: Browser page not initialized."
        if not query.strip():
            return "Error: Search query is empty."
        search_url = f"https://www.google.com/search?q={quote_plus(query.strip())}"
        try:
            await page.goto(search_url, wait_until="networkidle")
            return f"Search opened: {query.strip()}"
        except Exception as e:
            return f"Search error: {str(e)}"

class ClickTool(BaseTool):
    name = "click"
    description = "Click an element by CSS selector or coordinates."

    async def run(self, selector: str = None, x: int = None, y: int = None, page=None, **kwargs) -> str:
        self.log_action(selector=selector, x=x, y=y)
        if not page:
            return "Error: Browser page not initialized."
        
        try:
            if selector:
                await page.wait_for_selector(selector, timeout=5000)
                await page.click(selector)
                return f"Clicked element: {selector}"
            elif x is not None and y is not None:
                await page.mouse.click(x, y)
                return f"Clicked coordinates: {x}, {y}"
            return "Error: Neither selector nor coordinates provided for click."
        except Exception as e:
            return f"Click error: {str(e)}"

class ScrollTool(BaseTool):
    name = "scroll"
    description = "Scroll the browser page."

    async def run(self, direction: str = "down", amount: int = 500, page=None, **kwargs) -> str:
        self.log_action(direction=direction, amount=amount)
        if not page:
            return "Error: Browser page not initialized."
        
        try:
            px = amount if direction == "down" else -amount
            await page.evaluate(f"window.scrollBy(0, {px})")
            return f"Scrolled {direction} by {amount}px"
        except Exception as e:
            return f"Scroll error: {str(e)}"

class ReadPageTool(BaseTool):
    name = "read_page"
    description = "Extract text content from the current page."

    async def run(self, page=None, **kwargs) -> str:
        self.log_action()
        if not page:
            return "Error: Browser page not initialized."
        
        try:
            text = await page.inner_text("body")
            return text[:2000] + "..." if len(text) > 2000 else text
        except Exception as e:
            return f"Read error: {str(e)}"
