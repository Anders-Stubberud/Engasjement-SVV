import os
from pathlib import Path

import pandas as pd
import typer
from loguru import logger
from source.features_dir import estimated_registrations
from source import config
from source.config import MODE_AXLE_LOAD
from source.config import MODE_ESTIMATED_REGISTRATIONS
from source.config import MODE_VEHICLE_WEIGHT_74T
from source.config import MODE_VEHICLE_WEIGHT_WIM
from source.config import MODE_WIM_ROAD_WEAR_INDICATORS
from source.config import PROCESSED_DATA_DIR
from source.config import WIM_ROAD_WEAR_INDICATORS_DIR
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


def create_tex_for_images(image_dir, output_tex, subpath):
    # Get all PNG files in the directory
    image_files = [f for f in os.listdir(image_dir) if f.endswith(".png")]

    # Open the output .tex file for writing
    with open(output_tex, "w") as tex_file:
        # Iterate over the image files and create the input commands
        for image in image_files:
            image_path = os.path.join(image_dir, image)
            filename = image.split(".")[0]
            tex_file.write(
                """
\\begin{{figure}}[H]
    \\centering
    \\includegraphics[width=1\\linewidth]{{images/{subpath}/{filename}.png}}
\\end{{figure}}
            """.format(
                    subpath=subpath, filename=filename
                )
            )


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


def generate_latex_with_table(
    output_dir: Path,
    df: pd.DataFrame,
    title: str,
    filename: str,
    label: str = "tab:table",
    caption: str = "Table Caption",
) -> None:
    """
    Generate a LaTeX document with a table from a pandas DataFrame and compile it into a PDF.

    Args:
        output_dir (Path): The directory to save the output.
        df (pd.DataFrame): The DataFrame to include as a table.
        title (str): The title of the document.
        filename (str): The name of the LaTeX file (without extension).
        label (str): Label for the table.
        caption (str): Caption for the table.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(output_dir / "input.tex"):
        with open(output_dir / "input.tex", "w") as f:
            pass

    if not os.path.exists(output_dir / "validering.tex"):
        with open(output_dir / "input.tex", "w") as f:
            pass

    latex_file = output_dir / f"{filename}.tex"

    # Generate LaTeX code for the table
    latex_table_code = "\\begin{table}[H]\n"
    latex_table_code += "\\centering\n"
    latex_table_code += "\\resizebox{\\linewidth}{!}{\n"
    latex_table_code += df.to_latex(index=False, escape=False, float_format="%.2f")
    latex_table_code += "}\n"
    latex_table_code += f"\\caption{{{caption}}}\n"
    latex_table_code += "\\end{table}\n"

    # Write the LaTeX document
    with open(latex_file, "w") as f:
        f.write(r"\documentclass{article}" + "\n")
        f.write(r"\usepackage{graphicx}" + "\n")
        f.write(r"\usepackage{float}" + "\n")  # For H specifier
        f.write(r"\usepackage{booktabs}" + "\n")
        f.write(r"\usepackage[utf8]{inputenc}" + "\n")
        f.write(r"\usepackage{listings}" + "\n")
        f.write(r"\usepackage{graphicx}" + "\n")
        f.write(r"\usepackage{xcolor}" + "\n")
        f.write(r"\usepackage{amsmath}" + "\n")
        f.write(
            r"""
            \lstset{
                language=Python,
                backgroundcolor=\color{white}, % Set background color for code
                basicstyle=\ttfamily, % Set font for code
                keywordstyle=\color{blue}, % Color for keywords
                commentstyle=\color{green}, % Color for comments
                stringstyle=\color{red}, % Color for strings
                showstringspaces=false, % Don't show spaces in strings
                breaklines=true, % Break long lines
                frame=single % Add frame around code
            }
        """
            + "\n"
        )
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
        f.write(r"\input{input.tex}" + "\n")
        f.write(latex_table_code)
        f.write(r"\input{validering.tex}" + "\n")
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
    mode: int = 5,
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

    if should_run_task(mode, MODE_WIM_ROAD_WEAR_INDICATORS):
        generate_latex_with_table(
            output_dir=WIM_ROAD_WEAR_INDICATORS_DIR,
            df=pd.read_csv(PROCESSED_DATA_DIR / "WIM road wear factors/WIM_road_wear_factors.csv")[
                [
                    "Sted",
                    "B-faktor 5.6",
                    "B-faktor 7.5",
                    "N 5.6",
                    "N 7.5",
                    "ÅDTT 5.6",
                    "ÅDTT 7.5",
                    "E 5.6",
                    "E 7.5",
                    "C 5.6",
                    "C 7.5",
                ]
            ],
            filename="Supplerende_beregninger-forskjell_ved_endring_av_klassifisering_for_tunge_kjøretøy",
            title="Supplerende beregninger\nForskjell ved endring av klassifisering for tunge kjøretøy",
            label="tab:road-wear-indicators",
            caption="Forskjell ved endring av klassifisering for tunge kjøretøy",
        )

    if should_run_task(mode, MODE_ESTIMATED_REGISTRATIONS):

        create_tex_for_images(
            config.ESTIMATED_REGISTRATIONS_74T_DIR / f"{estimated_registrations.SUBPATH}/figures",
            config.ESTIMATED_REGISTRATIONS_74T_DIR / f"{estimated_registrations.SUBPATH}/imageinputs.tex",
            estimated_registrations.SUBPATH,
        )


if __name__ == "__main__":
    app()
