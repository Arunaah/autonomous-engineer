import sys

def calculate_grade(marks):
    """
    Calculate the grade based on marks.
    :param marks: List of marks
    :return: Grade
    """
    if not marks:
        return "No marks provided"

    average = sum(marks) / len(marks)
    if average >= 90:
        return "A"
    elif average >= 80:
        return "B"
    elif average >= 70:
        return "C"
    elif average >= 60:
        return "D"
    else:
        return "F"

def main():
    """
    Main function to calculate the grade of a student.
    """
    try:
        marks = [float(mark) for mark in sys.argv[1:]]
        grade = calculate_grade(marks)
        print(f"The student's grade is: {grade}")
    except ValueError:
        print("Error: Marks should be numbers.")
    except IndexError:
        print("Error: No marks provided.")

if __name__ == "__main__":
    main()