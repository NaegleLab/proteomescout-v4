import urllib

class Paginator():
    def __init__(self, form_schema, items_per_page):
        self.schema = form_schema
        self.current_page = 1
        self.items_per_page = items_per_page
        self.last_page = 1
        self.size = 0

    def parse_parameters(self, request):
        self.path_url = request.path_url
        try:
            self.current_page = int(request.GET['page'])
        except:
            self.current_page = 1

    def set_result_size(self, result_set_size):
        self.size = result_set_size
        self.last_page = result_set_size / self.items_per_page

        if result_set_size % self.items_per_page != 0:
            self.last_page += 1

    def get_page_url(self, page):
        copy_form_schema = self.schema.form_values.copy()

        for s in copy_form_schema.keys():
            if copy_form_schema[s] is None:
                del copy_form_schema[s]

        copy_form_schema['page'] = page
        return "%s?%s" % (self.path_url, urllib.urlencode(copy_form_schema))

    def get_pager_limits(self):
        return self.items_per_page, (self.current_page - 1) * self.items_per_page

    def has_next_page(self):
        return self.current_page < self.last_page

    def has_prev_page(self):
        return self.current_page > 1

    def next_page_url(self):
        return self.get_page_url(self.current_page + 1)

    def prev_page_url(self):
        return self.get_page_url(self.current_page - 1)

    def get_range(self):
        first = (self.current_page - 1) * self.items_per_page + 1
        last = self.current_page * self.items_per_page

        if first > self.size:
            first = self.size
        if last > self.size:
            last = self.size

        return "Showing %d - %d of %d results" % (first, last, self.size)

    def build(self):
        paginator_html = "<div class=\"pager\">"
        if self.has_prev_page():
            paginator_html += '<a href="%s">&lt;&lt;</a>\n' % (self.prev_page_url())
        else:
            paginator_html += '<span>&lt;&lt;</span>\n'

        for i in range(1, self.last_page+1):
            if i == self.current_page:
                paginator_html += '<span class="active_page">%d</span>\n' % (i)
            else:
                paginator_html += '<a href="%s">%d</a>\n' % (self.get_page_url(i), i)

        if self.has_next_page():
            paginator_html += '<a href="%s">&gt;&gt;</a>\n' % (self.next_page_url())
        else:
            paginator_html += '<span>&gt;&gt;</span>\n'

        paginator_html += "<div class=\"range\">%s</div>" % (self.get_range())
        paginator_html += "</div>"

        return paginator_html

