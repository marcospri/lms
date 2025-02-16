from pyramid.view import view_config

from lms.js_config_types import (
    APIAssignment,
    APICourse,
    AssignmentStats,
)
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.views.dashboard.base import get_request_course


class CourseViews:
    def __init__(self, request) -> None:
        self.request = request
        self.course_service = request.find_service(name="course")
        self.h_api = request.find_service(HAPI)

    @view_config(
        route_name="dashboard.api.course",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def course(self) -> APICourse:
        course = get_request_course(self.request, self.course_service)
        return {
            "id": course.id,
            "title": course.lms_name,
        }

    @view_config(
        route_name="dashboard.api.course.assignments.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def course_stats(self) -> list[APIAssignment]:
        course = get_request_course(self.request, self.course_service)

        stats = self.h_api.get_course_stats(
            # Annotations in the course group an any children
            [course.authority_provided_id]
            + [child.authority_provided_id for child in course.children]
        )
        # Organize the H stats by assignment ID for quick access
        stats_by_assignment = {s["assignment_id"]: s for s in stats}
        assignment_stats: list[APIAssignment] = []

        # Same course for all these assignments
        api_course = APICourse(id=course.id, title=course.lms_name)
        for assignment in course.assignments:
            if h_stats := stats_by_assignment.get(assignment.resource_link_id):
                stats = AssignmentStats(
                    annotations=h_stats["annotations"],
                    replies=h_stats["replies"],
                    last_activity=h_stats["last_activity"],
                )
            else:
                # Assignment with no annos, zeroing the stats
                stats = AssignmentStats(annotations=0, replies=0, last_activity=None)

            assignment_stats.append(
                APIAssignment(
                    id=assignment.id,
                    title=assignment.title,
                    course=api_course,
                    stats=stats,
                )
            )

        return assignment_stats
