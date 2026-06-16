# =====================================================
# GOALS
# =====================================================

@app.route("/goals")
@login_required
def goals():

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Goal.id.desc()
    ).all()

    return render_template(
        "goals/goals.html",
        goals=goals
    )

# =====================================================
# ADD GOAL
# =====================================================

@app.route(
    "/goal/add",
    methods=["POST"]
)
@login_required
def add_goal():

    title = request.form.get("title")

    progress = int(
        request.form.get(
            "progress",
            0
        )
    )

    goal = Goal(
        title=title,
        progress=progress,
        user_id=current_user.id
    )

    db.session.add(goal)

    db.session.commit()

    flash(
        "Meta creada correctamente.",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# EDIT GOAL
# =====================================================

@app.route(
    "/goal/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_goal(id):

    goal = Goal.query.get_or_404(id)

    if goal.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("goals")
        )

    if request.method == "POST":

        goal.title = request.form.get(
            "title"
        )

        goal.progress = int(
            request.form.get(
                "progress"
            )
        )

        db.session.commit()

        flash(
            "Meta actualizada.",
            "success"
        )

        return redirect(
            url_for("goals")
        )

    return render_template(
        "goals/edit_goal.html",
        goal=goal
    )

# =====================================================
# UPDATE GOAL PROGRESS
# =====================================================

@app.route(
    "/goal/update/<int:id>",
    methods=["POST"]
)
@login_required
def update_goal(id):

    goal = Goal.query.get_or_404(id)

    if goal.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("goals")
        )

    goal.progress = int(
        request.form.get(
            "progress"
        )
    )

    db.session.commit()

    flash(
        "Progreso actualizado.",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# DELETE GOAL
# =====================================================

@app.route("/goal/delete/<int:id>")
@login_required
def delete_goal(id):

    goal = Goal.query.get_or_404(id)

    if goal.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("goals")
        )

    db.session.delete(goal)

    db.session.commit()

    flash(
        "Meta eliminada.",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# MUSIC
# =====================================================

@app.route("/music")
@login_required
def music():

    return render_template(
        "music/music.html"
    )

# =====================================================
# PROFILE
# =====================================================

@app.route("/profile")
@login_required
def profile():

    task_count = Task.query.filter_by(
        user_id=current_user.id
    ).count()

    grade_count = Grade.query.filter_by(
        user_id=current_user.id
    ).count()

    goal_count = Goal.query.filter_by(
        user_id=current_user.id
    ).count()

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    average = 0

    if grades:

        average = round(
            sum(
                g.score
                for g in grades
            ) / len(grades),
            2
        )

    return render_template(
        "profile/profile.html",
        task_count=task_count,
        grade_count=grade_count,
        goal_count=goal_count,
        average=average
    )

# =====================================================
# STATS API
# =====================================================

@app.route("/stats")
@login_required
def stats():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    pending_tasks = len(
        [t for t in tasks if not t.completed]
    )

    completed_tasks = len(
        [t for t in tasks if t.completed]
    )

    average = 0

    if grades:

        average = round(
            sum(
                g.score
                for g in grades
            ) / len(grades),
            2
        )

    return {
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "average": average,
        "goals": len(goals)
    }

# =====================================================
# ERROR 404
# =====================================================

@app.errorhandler(404)
def page_not_found(error):

    return (
        render_template(
            "404.html"
        ),
        404
    )

# =====================================================
# ERROR 500
# =====================================================

@app.errorhandler(500)
def server_error(error):

    return (
        render_template(
            "500.html"
        ),
        500
    )

# =====================================================
# CREATE DATABASE
# =====================================================

with app.app_context():

    db.create_all()

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )
