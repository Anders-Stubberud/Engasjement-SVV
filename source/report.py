import os
from pathlib import Path

import typer
from loguru import logger

from source import config
from source.config import MODE_AXLE_LOAD
from source.config import MODE_VEHICLE_WEIGHT_74T
from source.config import MODE_VEHICLE_WEIGHT_WIM
from source.utils import should_run_task

app = typer.Typer()

sections_illustrasjoner_til_supplerende_analyser = [
    (
        "Total aksellastfordeling for separate akselkonfigurasjoner",
        [
            (
                "Enkeltaksel",
                [
                    "Total aksellastfordeling, enkeltaksel",
                    "Total aksellastfordeling, enkeltaksel, sammenliknet med N200",
                    "Total aksellastfordeling, enkeltaksel, sammenliknet med N200 og ekvivalensfaktor",
                ],
            ),
            (
                "Boggiaksel",
                [
                    "Total aksellastfordeling, boggiaksel",
                    "Total aksellastfordeling, boggiaksel, sammenliknet med N200",
                    "Total aksellastfordeling, boggiaksel, sammenliknet med N200 og ekvivalensfaktor",
                ],
            ),
            (
                "Trippelaksel",
                [
                    "Total aksellastfordeling, trippelaksel",
                    "Total aksellastfordeling, trippelaksel, sammenliknet med N200",
                    "Total aksellastfordeling, trippelaksel, sammenliknet med N200 og ekvivalensfaktor",
                ],
            ),
        ],
    ),
    (
        "Total aksellastfordeling for samtlige akselkonfigurasjoner",
        [
            "Total aksellastfordeling for samtlige akselkonfigurasjoner, barplot",
            "Total aksellastfordeling for samtlige akselkonfigurasjoner, lineplot",
            "Total aksellastfordeling for samtlige akselkonfigurasjoner, sammenliknet med N200, barplot",
            "Total aksellastfordeling for samtlige akselkonfigurasjoner, sammenliknet med N200, lineplot",
            "Total aksellastfordeling for samtlige akselkonfigurasjoner, sammenliknet med N200 og ekvivalensfaktor, barplot",
            "Total aksellastfordeling for samtlige akselkonfigurasjoner, sammenliknet med N200 og ekvivalensfaktor, lineplot",
        ],
    ),
]

sections_vehicle_weight = [
    (
        "Totalvekter, samtlige lokasjoner",
        ["Totalvekter, samtlige lokasjoner, lineplot"],
    ),
    (
        "Totalvekter, individuelle lokasjoner",
        [
            (
                "Totalvekter, Skibotn",
                [
                    "Totalvekter, Skibotn, lineplot",
                    "Totalvekter, Skibotn, barplot, 10 intervaller",
                    "Totalvekter, Skibotn, barplot, 20 intervaller",
                    "Totalvekter, Skibotn, barplot, 25 intervaller",
                ],
            ),
            (
                "Totalvekter, Verdal",
                [
                    "Totalvekter, Verdal, lineplot",
                    "Totalvekter, Verdal, barplot, 10 intervaller",
                    "Totalvekter, Verdal, barplot, 20 intervaller",
                    "Totalvekter, Verdal, barplot, 25 intervaller",
                ],
            ),
            (
                "Totalvekter, Ånestad(østgående)",
                [
                    "Totalvekter, Ånestad(østgående), lineplot",
                    "Totalvekter, Ånestad(østgående), barplot, 10 intervaller",
                    "Totalvekter, Ånestad(østgående), barplot, 20 intervaller",
                    "Totalvekter, Ånestad(østgående), barplot, 25 intervaller",
                ],
            ),
            (
                "Totalvekter, Ånestad(vestgående)",
                [
                    "Totalvekter, Ånestad(vestgående), lineplot",
                    "Totalvekter, Ånestad(vestgående), barplot, 10 intervaller",
                    "Totalvekter, Ånestad(vestgående), barplot, 20 intervaller",
                    "Totalvekter, Ånestad(vestgående), barplot, 25 intervaller",
                ],
            ),
            (
                "Totalvekter, Øysand",
                [
                    "Totalvekter, Øysand, lineplot",
                    "Totalvekter, Øysand, barplot, 10 intervaller",
                    "Totalvekter, Øysand, barplot, 20 intervaller",
                    "Totalvekter, Øysand, barplot, 25 intervaller",
                ],
            ),
        ],
    ),
]

sections_vehicle_weight_74t = [
    (
        "Totalvekter, samtlige konfigurasjoner",
        (
            "Totalvekter, samtlige konfigurasjoner",
            "Totalvekter, samtlige konfigurasjoner, individuelle bidrag",
        ),
    ),
    (
        "Totalvekter, individuelle konfigurasjoner",
        (
            "Totalvekter, 3-akslet trekkvogn med 4-akslet tilhenger (60T)",
            "Totalvekter, 3-akslet trekkvogn med 5-akslet tilhenger (65T)",
            "Totalvekter, 4-akslet trekkvogn med 4-akslet tilhenger (68T)",
            "Totalvekter, 4-akslet trekkvogn med 5-akslet tilhenger (74T)",
        ),
    ),
]


def is_flat(iterable: list) -> bool:
    """Check if a list or tuple contains no nested lists or tuples."""
    return all(not isinstance(item, (list, tuple)) for item in iterable)


def generate_latex_catalog(
    image_dir: Path, output_dir: Path, sections: list, title: str, filename: str
) -> None:
    """
    Generate a LaTeX document cataloging the images from a directory with a TOC.
    Saves the catalog as a PDF in the output directory.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    image_extensions = [".png", ".jpg", ".jpeg", ".pdf"]
    images = [
        file
        for file in os.listdir(image_dir)
        if any(file.endswith(ext) for ext in image_extensions)
    ]
    images.sort()

    latex_file = output_dir / f"{filename}.tex"

    with open(latex_file, "w") as f:
        f.write(r"\documentclass{article}" + "\n")
        f.write(r"\usepackage{graphicx}" + "\n")
        f.write(r"\usepackage{float}" + "\n")  # For H specifier
        f.write(r"\usepackage{tocloft}" + "\n")  # Optional: for TOC styling
        f.write(r"\usepackage[norsk]{babel}" + "\n")  # Norwegian language
        f.write(
            r"\usepackage[a4paper, left=20mm, right=20mm, top=25mm, bottom=25mm]{geometry}" + "\n"
        )
        f.write(
            r"\usepackage[linkcolor=black, urlcolor=black, citecolor=black, hidelinks]{hyperref}"
            + "\n"
        )
        f.write(r"\begin{document}" + "\n")
        f.write(f"\\title{{{title.replace('\n', '\\\\')}}}\n")
        f.write(r"\author{Anders V. Stubberud}" + "\n")
        f.write(r"\maketitle" + "\n")
        f.write(r"\tableofcontents" + "\n")
        f.write(r"\newpage" + "\n")

        for section_title, subsections in sections:
            f.write(r"\section{" + section_title + "}" + "\n")
            if is_flat(subsections):  # Special handling subsections without subsubsections
                for subsection_title in subsections:
                    f.write(r"\subsection{" + subsection_title + "}" + "\n")
                    img_filename = subsection_title + ".png"
                    if img_filename in images:
                        f.write(r"\begin{figure}[H]" + "\n")
                        f.write(r"\centering" + "\n")
                        f.write(
                            r"\includegraphics[width=\textwidth]{"
                            + str(image_dir / img_filename)
                            + "}"
                            + "\n"
                        )
                        f.write(r"\end{figure}" + "\n")
            else:
                for subsection_title, subsubsections in (
                    subsections if isinstance(subsections[0], tuple) else [(None, subsections)]
                ):
                    if subsection_title:
                        f.write(r"\subsection{" + subsection_title + "}" + "\n")
                    for subsubsection_title in subsubsections:
                        f.write(r"\subsubsection{" + subsubsection_title + "}" + "\n")
                        img_filename = subsubsection_title + ".png"
                        if img_filename in images:
                            f.write(r"\begin{figure}[H]" + "\n")
                            f.write(r"\centering" + "\n")
                            f.write(
                                r"\includegraphics[width=\textwidth]{"
                                + str(image_dir / img_filename)
                                + "}"
                                + "\n"
                            )
                            f.write(r"\end{figure}" + "\n")

        f.write(r"\end{document}" + "\n")

    try:
        os.system(f"pdflatex -output-directory={output_dir} {latex_file}")
        os.system(f"pdflatex -output-directory={output_dir} {latex_file}")
    except Exception as e:
        logger.error(f"LaTeX compilation failed: {e}")

    for ext in ["aux", "log", "toc", "out"]:
        temp_file = latex_file.with_suffix(f".{ext}")
        if temp_file.exists():
            os.remove(temp_file)


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = config.AXLE_LOAD_W_N200_AND_ESAL_FIGURES_DIR,
    output_path: Path = config.AXLE_LOAD_W_N200_AND_ESAL_DIR,
    mode: int = 0,
    # ----------------------------------------------
):

    if should_run_task(mode, MODE_AXLE_LOAD):
        generate_latex_catalog(
            image_dir=config.AXLE_LOAD_W_N200_AND_ESAL_FIGURES_DIR,
            output_dir=config.AXLE_LOAD_W_N200_AND_ESAL_DIR,
            sections=sections_illustrasjoner_til_supplerende_analyser,
            title="Illustrasjoner til supplerende analyser\nAksellastfordelinger",
            filename="Illustrasjoner-til-supplerende-analyser-Aksellastfordelinger",
        )

    if should_run_task(mode, MODE_VEHICLE_WEIGHT_WIM):
        generate_latex_catalog(
            image_dir=config.VEHICLE_WEIGHT_FIGURES_DIR_WIM,
            output_dir=config.VEHICLE_WEIGHT_DIR_WIM,
            sections=sections_vehicle_weight,
            title="Illustrasjoner til supplerende analyser\nTotalvekter",
            filename="Illustrasjoner-til-supplerende-analyser-Totalvekter",
        )

    if should_run_task(mode, MODE_VEHICLE_WEIGHT_74T):
        generate_latex_catalog(
            image_dir=config.VEHICLE_WEIGHT_FIGURES_DIR_74T,
            output_dir=config.VEHICLE_WEIGHT_DIR_74T,
            sections=sections_vehicle_weight_74t,
            title="Totalvekter fra 74T prøveordningen",
            filename="Totalvekter-fra-74T-prøveordningen",
        )


if __name__ == "__main__":
    app()
