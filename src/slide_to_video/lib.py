import os


from .project import Project, ProjectConfig


def slide_to_video(
    *,
    project_config: ProjectConfig,
):
    # Create the output directory if it does not exist
    output_dir = project_config["output_dir"]
    if os.path.exists(output_dir):
        project_file = f"{output_dir}/project.yaml"
        if not os.path.exists(project_file):
            # remove the directory
            os.system(f"rm -rf {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    if "script_dict" in project_config:
        replace_dict = {}
        script_dict = project_config["script_dict"]
        with open(script_dict, "r") as f:
            lines = f.readlines()
            for line in lines:
                original_text, new_text = line.strip().split(":")
                replace_dict[original_text.strip()] = new_text.strip()
        project_config["script_dict"] = replace_dict

    project = Project(
        name="project",
        config=project_config,
    )
    project.build()
    project.save()
