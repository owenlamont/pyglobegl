import marimo


__generated_with = "0.19.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    from pyglobegl import GlobeWidget

    return mo.ui.anywidget(GlobeWidget())


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
