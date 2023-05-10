"""The Core’s template tags for generating paginations."""
from django import template

register = template.Library()


@register.simple_tag
def pagination_generate_indexes(length: int, current: int, delta: int = 2) -> list[int]:
    """Returns a list of page indexes for pagination: This list will not excceed
    a suitable length for pagination. If the number of pages is larger than this
    suitable length, the list of indexes will contain -1 which indicates the
    omission of some page indexes and may be rendered as ellipsis.

    Arguments:
        length: int
            Specifies the total length for the pagination.
        current: int
            Specifies the current index for pagination.

    Returns:
        A list of page numbers with the special case of -1 for omitted numbers.

    Examples:
        pagination(20, 1) -> [1, 2, 3, -1, 20]
        pagination(20, 2) -> [1, 2, 3, 4, -1, 20]
        pagination(20, 7) -> [1, -1, 5, 6, 7, 8, 9, -1, 20]
        pagination(20, 19) -> [1, -1, 17, 18, 19, 20]

    Template usage:
        {% generate_pagination_indexes paging.paginator.num_pages paging.cur_page as pagination_indexes %}
        {% for i in pagination_indexes %}
            {% if i < 0 %}
                <li class="ellipsis"></li>
            {% else %}
                {% if i == paging.cur_page %}
                    <li class="item--active">{{i}}</li>
                {% else %}
                    <li>{{i}}</li>
                {% endif %}
            {% endif %}
        {% endfor %}
    """
    length = int(length)
    current = int(current)
    delta = int(delta)

    # This is a sanity check while developing which can be safely removed in production.
    assert length > 0  # nosec
    assert current > 0 and current <= length  # nosec

    left = current - delta
    right = current + delta + 1

    indexes = []
    last = 0
    for i in range(1, length + 1):
        # select suitable indexes
        if i == 1 or i == length or (i >= left and i < right):
            if i != last + 1:
                # append marker for omitted indexes
                indexes.append(-1)
            # append index
            indexes.append(i)
            # remember last suitable index
            last = i

    return indexes
