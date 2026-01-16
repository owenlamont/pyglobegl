import solara

from pyglobegl import GlobeWidget


@solara.component
def page():
    """Render the globe widget in Solara.

    Returns:
        The root Solara element for the page.
    """
    with solara.Column() as main:
        solara.display(GlobeWidget())
    return main
