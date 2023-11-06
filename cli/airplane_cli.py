"""
ICARUS CLI for Airplane Analysis

Raises:
    NotImplementedError: _description_

Returns:
    None: None
"""
import time
from typing import Any

import jsonpickle
import jsonpickle.ext.pandas as jsonpickle_pd
import numpy as np
from inquirer import Checkbox
from inquirer import List
from inquirer import Path
from inquirer import prompt
from inquirer import Text

from .cli_home import cli_home
from ICARUS.Core.struct import Struct
from ICARUS.Database import DB
from ICARUS.Environment.definition import EARTH_ISA
from ICARUS.Environment.definition import Environment
from ICARUS.Input_Output.XFLR5.parser import parse_xfl_project
from ICARUS.Solvers.Airplane.gnvp3 import get_gnvp3
from ICARUS.Solvers.Airplane.gnvp7 import get_gnvp7
from ICARUS.Solvers.Airplane.lspt import get_lspt
from ICARUS.Vehicle.plane import Airplane
from ICARUS.Workers.solver import Solver

jsonpickle_pd.register_handlers()


def ask_num_airplanes() -> int:
    no_question: list[Text] = [
        Text("num_airplanes", message="How many airplanes do you want to run", autocomplete=1),
    ]
    answer: dict[Any, Any] | None = prompt(no_question)
    if answer is None:
        print("Exited by User")
        exit()
    try:
        if int(answer["num_airplanes"]) < 1:
            print(f"Answer {answer['num_airplanes']} doesnt make sense")
            return ask_num_airplanes()
        return int(answer["num_airplanes"])
    except ValueError:
        print(f"Answer {answer['num_airplanes']} doesnt make sense")
        return ask_num_airplanes()


def get_airplane_file(load_from: str) -> Airplane:
    file_question: list[Path] = [
        Path(
            "airplane_file",
            message="Specify the Full Path to the Airplane File",
            path_type=Path.FILE,
        ),
    ]
    answers: dict[Any, Any] | None = prompt(file_question)
    if answers is None:
        print("Exited by User")
        exit()
    else:
        if load_from == "xflr5":
            plane: Airplane = parse_xfl_project(answers["airplane_file"])
            return plane
        elif load_from == "avl":
            print("Not implemented yet")
            raise NotImplementedError
            # plane: Airplane = parse_avl_project(answers["airf_file"])
        elif load_from == "json":
            try:
                with open(answers["airplane_file"], encoding="UTF-8") as f:
                    json_obj: str = f.read()
                    try:
                        plane: Airplane = jsonpickle.decode(json_obj)  # type: ignore
                        return plane
                    except Exception as error:
                        print(f"Error decoding Plane object! Got error {error}")
                        return get_airplane_file(load_from)
            except FileNotFoundError:
                print(f"File {answers['airplane_file']} not found")
                return get_airplane_file(load_from)
        else:
            print("Error")
            return get_airplane_file(load_from)


def get_airplane_db() -> Airplane:
    planes: list[str] = DB.vehicles_db.get_planenames()
    airplane_question: list[List] = [
        List(
            "plane_name",
            message="Which airfoil do you want to load",
            choices=[plane_name for plane_name in planes],
        ),
    ]
    answer: dict[Any, Any] | None = prompt(airplane_question)
    if answer is None:
        print("Exited by User")
        exit()

    try:
        airplane: Airplane = DB.vehicles_db.planes[answer["plane_name"]]
        return airplane
    except Exception as e:
        print(e)
        return get_airplane_db()


def select_airplane_source() -> Airplane:
    airplane_source_question: list[List] = [
        List(
            "airplane_source",
            message="Where do you want to get the airplane from",
            choices=["File", "Database", "Load from XFLR5", "Load from AVL (NOT IMPLEMENTED YET)"],
        ),
    ]

    answer: dict[Any, Any] | None = prompt(airplane_source_question)
    if answer is None:
        print("Exited by User")
        exit()
    if answer["airplane_source"] == "File":
        return get_airplane_file(load_from="json")
    elif answer["airplane_source"] == "Database":
        return get_airplane_db()
    elif answer["airplane_source"] == "Load from XFLR5":
        return get_airplane_file(load_from="xflr5")
    elif answer["airplane_source"] == "Load from AVL":
        return get_airplane_file(load_from="avl")
    else:
        print("Error")
        return select_airplane_source()


def set_analysis(solver: Solver) -> None:
    analyses: list[str] = solver.available_analyses_names(verbose=True)
    analyses_quest: list[List] = [
        List(
            "analysis",
            message="Which analysis do you want to perform",
            choices=[analysis for analysis in analyses],
        ),
    ]
    answer: dict[Any, Any] | None = prompt(analyses_quest)
    if answer is None:
        print("Exited by User")
        exit()
    if answer["analysis"] in analyses:
        solver.set_analyses(answer["analysis"])
    else:
        print("Error")
        return set_analysis(solver)


input_options = {
    float: "float",
    int: "int",
    bool: "bool",
    str: "text",
    list[float]: "list_float",
    list[int]: "list_int",
    list[str]: "list_str",
    list[bool]: "list_bool",
    list[str]: "list_str",
}


def get_option(
    option_name: str,
    question_type: str,
) -> dict[str, Any]:
    if question_type.startswith("list_"):
        quest: Text = Text(
            f"{option_name}",
            message=f"{option_name} (Multiple Values Must be seperated with ','. You can also specify a range as a:b:c where a and b are the endpoints and c the step )",
        )
    else:
        quest = Text(
            f"{option_name}",
            message=f"{option_name} = ",
        )

    answer: dict[str, Any] | None = prompt([quest])
    if answer is None:
        print("Exited by User")
        exit()

    try:
        if question_type == "float":
            answer[option_name] = float(answer[option_name])
        elif question_type == "int":
            answer[option_name] = int(answer[option_name])
        elif question_type == "bool":
            answer[option_name] = bool(answer[option_name])
        elif question_type == "text":
            answer[option_name] = str(answer[option_name])
        elif question_type == "list_float":
            # Check if the user specified a range
            if ":" in answer[option_name]:
                a, b, c = answer[option_name].split(":")
                answer[option_name] = np.linspace(float(a), float(b), num=int(c))
            else:
                answer[option_name] = [float(x) for x in answer[option_name].split(",")]
        elif question_type == "list_int":
            answer[option_name] = [int(x) for x in answer[option_name].split(",")]
        elif question_type == "list_bool":
            answer[option_name] = [bool(x) for x in answer[option_name].split(",")]
        elif question_type == "list_str":
            answer[option_name] = [str(x) for x in answer[option_name].split(",")]
    except Exception as e:
        print(answer)
        print("Error Getting Answer! Try Again")
        print(f"Got error {e}")
        import sys

        sys.exit()
    return answer


def set_environment_options(earth: Environment) -> Environment:
    """
    Function to set the options for the environment. It first displays the
    environment options and then asks the user if he wants to change any of
    them. The user can set the values manually or he can use the built in
    functions to define them from the altitude

    Args:
        earth (Environment): earth default environment

    Returns:
        Environment: environment to use
    """
    print("########################################################################")
    print("Environment:")
    print(earth)
    print("########################################################################")

    # Ask whether to change the values
    change_prompt: list[List] = [
        List(
            "change",
            message="Do you want to change any of the environment parameters",
            choices=["Yes", "No"],
        ),
    ]

    choice: dict[Any, Any] | None = prompt(change_prompt)
    if choice is None:
        print("Exited by User")
        exit()
    if choice["change"] == "Yes":
        # Ask whether to input the values manually or use the built in functions
        # Get the values manually
        environment_quest: list[Text] = [
            Text(
                "temperature",
                message="Temperature = ",
            ),
            Text(
                "altitude",
                message="Altitude = ",
            ),
        ]

        answer: dict[Any, Any] | None = prompt(environment_quest)
        if answer is None:
            print("Exited by User")
            exit()
        try:
            TEMP = float(answer["temperature"])
            ALLTITUDE = float(answer["altitude"])
            earth._set_pressure_from_altitude_and_temperature(
                ALLTITUDE,
                TEMP,
            )
            return earth
        except KeyError:
            print("Error setting environment! Try Again")
            return set_environment_options(earth)
    elif choice["change"] == "No":
        return earth
    else:
        print("Error! Got invalid answer")
        return set_environment_options(earth)


def get_environment() -> Environment:
    environment_quest: list[List] = [
        List(
            "environment",
            message="Which environment do you want to use",
            choices=["EARTH_ISA"],
        ),
    ]
    answer: dict[Any, Any] | None = prompt(environment_quest)
    if answer is None:
        print("Exited by User")
        exit()
    if answer["environment"] == "EARTH_ISA":
        return set_environment_options(EARTH_ISA)
    else:
        print("Error")
        return get_environment()


def get_2D_polars_solver() -> str:
    solver_quest: list[List] = [
        List(
            "solver",
            message="Which solver do you want to use! Be aware that in order to integrate the 2D polars in any analysis you need to have first run the 2D analysis for the airfoils",
            choices=["Xfoil", "Foil2Wake", "XFLR", "Use-All-Hierarchical"],
        ),
    ]
    answer: dict[Any, Any] | None = prompt(solver_quest)
    if answer is None:
        print("Exited by User")
        exit()
    if answer["solver"] == "Xfoil":
        return "Xfoil"
    elif answer["solver"] == "Foil2Wake":
        return "Foil2Wake"
    elif answer["solver"] == "XFLR":
        return "XFLR"
    elif answer["solver"] == "Use-All-Hierarchical":
        print("We will interpolate the 2D polars from all solvers in the Database.")
        print("You must specify the order of preference of the solvers. A solver with")
        print("a lower number will have a higher priority. For example if you specify")
        print("that Xfoil has priority 1 and Foil2Wake has priority 2, then the 2D")
        print("polars from Xfoil will be used if they exist. If they dont exist, the")
        print("2D polars from Foil2Wake will be used")

        solvers: list[str] = ["Xfoil", "Foil2Wake", "XFLR"]
        # Prompt for the order of preference of the solvers as a number from 1 to len(solvers)
        solver_pref_quest: list[Text] = [
            Text(
                f"{solver}",
                message=f"{solver} = ",
            )
            for solver in solvers
        ]
        answer = prompt(solver_pref_quest)
        if answer is None:
            print("Exited by User")
            exit()

        print("This is not fully implemented yet, so we will just use the first priority solver")

        # rank solvers by priority
        solver_ranking: dict[str, float] = {}
        for solver in solvers:
            solver_ranking[solver] = answer[solver]
        solver_ranking = dict(sorted(solver_ranking.items(), key=lambda item: item[1]))

        # return the first solver
        return list(solver_ranking.keys())[0]

    else:
        print("Error")
        return get_2D_polars_solver()


def set_analysis_options(solver: Solver, airfoil: Airplane) -> None:
    all_options: Struct = solver.get_analysis_options(verbose=True)
    options = Struct()
    answers: dict[str, Any] = {}
    for option in all_options.keys():
        if option == "environment":
            answers[option] = get_environment()
            continue
        elif option == "solver2D":
            answers[option] = get_2D_polars_solver()
            continue
        options[option] = all_options[option]

        try:
            question_type = input_options[options[option].option_type]
        except KeyError:
            print(f"Option {option} has an invalid type")
            continue

        answer = get_option(option, question_type)
        answers[option] = answer[option]

    try:
        solver.set_analysis_options(answers)
        print("Options set")
        _: Struct = solver.get_analysis_options(verbose=True)

    except:
        print("Unable to set options! Try Again")
        return set_analysis_options(solver, airfoil)


def set_solver_parameters(solver: Solver) -> None:
    parameters: Struct = solver.get_solver_parameters(verbose=True)
    change_prompt: list[List] = [
        List(
            "change",
            message="Do you want to change any of the solver parameters",
            choices=["Yes", "No"],
        ),
    ]
    choice: dict[Any, Any] | None = prompt(change_prompt)
    if choice is None:
        print("Exited by User")
        exit()
    if choice["change"] == "Yes":
        parameters_quest: list[Text] = [
            Text(
                f"{parameter}",
                message=f"{parameter} = ",
            )
            for parameter in parameters.keys()
        ]
        answer: dict[Any, Any] | None = prompt(parameters_quest)
        if answer is None:
            print("Exited by User")
            exit()
        try:
            solver.set_solver_parameters(answer)
        except:
            print("Unable to set parameters! Try Again")
            return set_solver_parameters(solver)


def airplane_cli(return_home: bool = False) -> None:
    """2D CLI"""
    start_time: float = time.time()

    N: int = ask_num_airplanes()
    if N < 1:
        print("N must be greater than 0")
        return

    airplanes: list[Airplane] = []

    calc_gnvp_3: dict[str, bool] = {}
    gnvp_3_solvers: dict[str, Solver] = {}

    calc_gnvp_7: dict[str, bool] = {}
    gnvp_7_solvers: dict[str, Solver] = {}

    calc_lspt: dict[str, bool] = {}
    lspt_solvers: dict[str, Solver] = {}

    for i in range(N):
        print("\n")
        vehicle: Airplane = select_airplane_source()
        airplanes.append(vehicle)

        select_solver_quest: list[Checkbox] = [
            Checkbox(
                "solver",
                message="Which solvers do you want to run",
                choices=["GNVP3", "GNVP7", "LSPT"],
            ),
        ]
        answer: dict[Any, Any] | None = prompt(select_solver_quest)
        if answer is None:
            print("Error")
            return

        if "GNVP3" in answer["solver"]:
            calc_gnvp_3[vehicle.name] = True

            # Get Solver
            gnvp_3_solvers[vehicle.name] = get_gnvp3()
            set_analysis(gnvp_3_solvers[vehicle.name])
            set_analysis_options(gnvp_3_solvers[vehicle.name], vehicle)
            set_solver_parameters(gnvp_3_solvers[vehicle.name])
        else:
            calc_gnvp_3[vehicle.name] = False

        if "GNVP7" in answer["solver"]:
            calc_gnvp_7[vehicle.name] = True

            # Get Solver
            gnvp_7_solvers[vehicle.name] = get_gnvp7()
            set_analysis(gnvp_7_solvers[vehicle.name])
            set_analysis_options(gnvp_7_solvers[vehicle.name], vehicle)
            set_solver_parameters(gnvp_7_solvers[vehicle.name])
        else:
            calc_gnvp_7[vehicle.name] = False

        if "LSPT" in answer["solver"]:
            calc_lspt[vehicle.name] = True

            # Get Solver
            lspt_solvers[vehicle.name] = get_lspt()
            set_analysis(lspt_solvers[vehicle.name])
            set_analysis_options(lspt_solvers[vehicle.name], vehicle)
            set_solver_parameters(lspt_solvers[vehicle.name])
        else:
            calc_lspt[vehicle.name] = False

    #####################################  START Calculations #####################################
    for vehicle in airplanes:
        ariplane_stime: float = time.time()
        print(f"\nRunning Airplane {vehicle.name}\n")

        # GNVP3
        if calc_gnvp_3[vehicle.name]:
            gnvp_3_stime: float = time.time()

            # Set Solver Options and Parameters
            gnvp3_s: Solver = gnvp_3_solvers[vehicle.name]
            gnvp3_options: Struct = gnvp3_s.get_analysis_options(verbose=True)
            gnvp3_options.plane.value = vehicle

            # Run Solver
            gnvp_3_solvers[vehicle.name].run()

            # Get Results
            _ = gnvp_3_solvers[vehicle.name].get_results()

            gnvp_3_etime: float = time.time()
            print(f"Foil2Wake completed in {gnvp_3_etime - gnvp_3_stime} seconds")

        # GNVP7
        if calc_gnvp_7[vehicle.name]:
            gnvp_7_stime: float = time.time()

            # Set Solver Options and Parameters
            gnvp_7: Solver = gnvp_7_solvers[vehicle.name]
            gnvp_7_options: Struct = gnvp_7.get_analysis_options(verbose=True)
            gnvp_7_options.plane.value = vehicle

            # Run Solver and Get Results
            gnvp_7_solvers[vehicle.name].run()

            gnvp_7_etime: float = time.time()
            print(f"XFoil completed in {gnvp_7_etime - gnvp_7_stime} seconds")

        # LSPT
        if calc_lspt[vehicle.name]:
            lspt_stime: float = time.time()

            # Set Solver Options and Parameters
            lspt: Solver = lspt_solvers[vehicle.name]
            lspt_options: Struct = lspt.get_analysis_options(verbose=True)
            lspt_options.plane.value = vehicle

            # Run Solver and Get Results
            lspt_solvers[vehicle.name].run()

            lspt_etime: float = time.time()
            print(f"XFoil completed in {lspt_etime - lspt_stime} seconds")

        airplane_etime: float = time.time()
        print(
            f"Airplane {vehicle} completed in {airplane_etime - ariplane_stime} seconds",
        )
    ##################################### END Calculations ########################################

    end_time: float = time.time()
    print(f"Total time: {end_time - start_time}")
    print("########################################################################")
    print("Program Terminated")
    print("########################################################################")

    if return_home:
        cli_home()


if __name__ == "__main__":
    airplane_cli()
