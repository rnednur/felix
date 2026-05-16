"""
Initialize the tool system

Registers all available tools and sets up the tool catalog.
"""
import logging
from app.tools.catalog import get_tool_catalog, init_tool_catalog
from app.tools.tool_router import init_tool_router
from app.tools.primitives import (
    ReadDatasetTool,
    ExecuteSQLTool,
    CalculateStatsTool,
    GenerateChartTool,
    AdvancedVisualizationTool,
    StatisticalPlotTool,
    HTMLReportTool,
    PDFReportTool,
    DataProfilingTool,
    HypothesisTestingTool
)

logger = logging.getLogger("tool.init")


def initialize_tools():
    """
    Initialize the tool system

    Registers all available tools in the catalog.
    """
    logger.info("Initializing tool system...")

    # Initialize catalog
    catalog = init_tool_catalog()

    # Register data access tools
    catalog.register_tool(
        ReadDatasetTool(),
        enabled=True,
        access_level="public",
        cost_credits=1
    )

    catalog.register_tool(
        ExecuteSQLTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=60,
        cost_credits=2
    )

    # Register computation tools
    catalog.register_tool(
        CalculateStatsTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=30,
        cost_credits=3
    )

    # Register visualization tools
    catalog.register_tool(
        GenerateChartTool(),
        enabled=True,
        access_level="public",
        cost_credits=2
    )

    catalog.register_tool(
        AdvancedVisualizationTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=20,
        cost_credits=5
    )

    catalog.register_tool(
        StatisticalPlotTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=20,
        cost_credits=4
    )

    # Register analysis tools
    catalog.register_tool(
        DataProfilingTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=10,
        cost_credits=10
    )

    catalog.register_tool(
        HypothesisTestingTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=30,
        cost_credits=3
    )

    # Register export/report tools
    catalog.register_tool(
        HTMLReportTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=10,
        cost_credits=5
    )

    catalog.register_tool(
        PDFReportTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=10,
        cost_credits=8
    )

    # Initialize router
    init_tool_router(catalog)

    logger.info(f"Tool system initialized: {catalog.get_tool_count()} tools registered")
    logger.info(f"Categories: {', '.join(catalog.get_categories())}")

    return catalog


def get_initialized_catalog():
    """
    Get the initialized catalog (initializes if needed)

    Returns:
        ToolCatalog
    """
    catalog = get_tool_catalog()

    if catalog.get_tool_count() == 0:
        logger.info("Tool catalog empty, initializing...")
        initialize_tools()

    return catalog
