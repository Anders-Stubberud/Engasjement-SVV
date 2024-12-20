import os
from pathlib import Path

import typer
from loguru import logger

from source import config

app = typer.Typer()


def generate_latex_catalog(image_dir: Path, output_dir: Path):
    """
    Generate a LaTeX document cataloging the images from a directory with a TOC.
    Saves the catalog as a PDF in the output directory.
    """
    # Create output directory if it does not exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect images from the directory
    image_extensions = [".png", ".jpg", ".jpeg", ".pdf"]
    images = [
        file
        for file in os.listdir(image_dir)
        if any(file.endswith(ext) for ext in image_extensions)
    ]

    # Sort images (optional, depending on your preferred order)
    images.sort()

    # LaTeX document content
    latex_file = output_dir / "Illustrasjoner-til-supplerende-analyser.tex"

    # Start writing LaTeX file, overwriting if it exists
    with open(latex_file, "w") as f:
        f.write(r"\documentclass{article}" + "\n")
        f.write(r"\usepackage{graphicx}" + "\n")
        f.write(r"\usepackage{float}" + "\n")  # For H specifier
        f.write(r"\usepackage{tocloft}" + "\n")  # Optional: for TOC styling
        f.write(r"\usepackage[norsk]{babel}" + "\n")  # Norwegian language
        f.write(
            r"\usepackage[a4paper, left=20mm, right=20mm, top=25mm, bottom=25mm]{geometry}" + "\n"
        )  # Adjusted margins

        # Configure hyperref to remove boxes and set link color to black
        f.write(
            r"\usepackage[linkcolor=black, urlcolor=black, citecolor=black, hidelinks]{hyperref}"
            + "\n"
        )

        f.write(r"\begin{document}" + "\n")

        # Title and author
        f.write(r"\title{Illustrasjoner til supplerende analyser}" + "\n")
        f.write(r"\author{Anders V. Stubberud}" + "\n")
        f.write(r"\maketitle" + "\n")

        # Generate Table of Contents
        f.write(r"\tableofcontents" + "\n")
        f.write(r"\newpage" + "\n")

        # Major sections with subsections and subsubsections
        sections = [
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

        # Replace this section where you process subsections and subsubsections
        # for "Total aksellastfordeling for samtlige akselkonfigurasjoner"
        for section_title, subsections in sections:
            # Write section title and add to TOC
            f.write(r"\section{" + section_title + "}" + "\n")

            # Special handling for this section
            if section_title == "Total aksellastfordeling for samtlige akselkonfigurasjoner":
                # This section should directly list subsections, not subsubsections
                for subsection_title in subsections:
                    # Write subsection (not subsubsection)
                    f.write(r"\subsection{" + subsection_title + "}" + "\n")

                    # Insert image (assuming images are named according to the subsection title with .png extension)
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
                        # f.write(r"\caption{" + subsection_title + "}" + "\n")
                        f.write(r"\end{figure}" + "\n")
            else:
                # Loop through the rest of the sections as normal (subsubsection structure)
                for subsection_title, subsubsections in (
                    subsections if isinstance(subsections[0], tuple) else [(None, subsections)]
                ):
                    # Write subsection
                    if subsection_title:
                        f.write(r"\subsection{" + subsection_title + "}" + "\n")

                    for subsubsection_title in subsubsections:
                        # Write subsubsection and corresponding image
                        f.write(r"\subsubsection{" + subsubsection_title + "}" + "\n")
                        # Insert image (assuming images are named according to the subsubsection title with .png extension)
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
                            # f.write(r"\caption{" + subsubsection_title + "}" + "\n")
                            f.write(r"\end{figure}" + "\n")

        f.write(r"\end{document}" + "\n")

    # Compile LaTeX to PDF using pdflatex (system command)
    try:
        os.system(f"pdflatex -output-directory={output_dir} {latex_file}")
        os.system(
            f"pdflatex -output-directory={output_dir} {latex_file}"
        )  # Second run to generate TOC correctly
    except Exception as e:
        logger.error(f"LaTeX compilation failed: {e}")

    # Optionally, remove the .aux, .log, .toc files generated by LaTeX
    for ext in ["aux", "log", "toc", "out"]:
        temp_file = latex_file.with_suffix(f".{ext}")
        if temp_file.exists():
            os.remove(temp_file)


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = config.FIGURES_DIR,
    output_path: Path = config.REPORTS_DIR,
    # ----------------------------------------------
):
    # ---- LaTeX Catalog Generation ----
    generate_latex_catalog(input_path, output_path)


if __name__ == "__main__":
    app()
