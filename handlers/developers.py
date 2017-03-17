import tornado.web

from base import BaseHandler

from models import App

class NewAppHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        return self.render("developers/new-api-application.html", title='', description='', redirect_url='')

    @tornado.web.authenticated
    def post(self):
        current_user = self.get_current_user_object()
        title = self.get_argument('title', '').strip()
        description = self.get_argument('description', '').strip()
        redirect_url = self.get_argument('redirect_url', '').strip()
        new_app = App(user_id=current_user.id, title=title, description=description, redirect_url=redirect_url)
        if not new_app.save():
            self.add_errors(new_app.errors)
            return self.render("developers/new-api-application.html", title=title, description=description, redirect_url=redirect_url)
            
        return self.redirect('/developers/view-app/%s' % (new_app.id))


class PageHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, template='index'):
        return self.render("developers/%s.html" % template)


class AppsListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        current_user = self.get_current_user_object()
        api_apps = App.where('user_id = %s', current_user.id)
        return self.render("developers/apps.html", apps=api_apps)


class ViewAppHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, app_id):
        current_user = self.get_current_user_object()
        api_app = App.get('id = %s and user_id = %s', int(app_id), current_user.id)
        if not api_app:
            return self.redirect("/developers")
        return self.render("developers/view-app.html", app=api_app)
    
class EditAppHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, app_id):
        current_user = self.get_current_user_object()
        api_app = App.get('id = %s and user_id = %s', int(app_id), current_user.id)
        if not api_app:
            return self.redirect("/developers")
        return self.render("developers/edit-app.html", app=api_app)

    @tornado.web.authenticated
    def post(self, app_id):
        current_user = self.get_current_user_object()
        api_app = App.get('id = %s and user_id = %s', int(app_id), current_user.id)
        if not api_app:
            return self.redirect("/developers")
        api_app.title = self.get_argument('title', '').strip()
        api_app.description = self.get_argument('description', '').strip()
        api_app.redirect_url = self.get_argument('redirect_url', '').strip()
        if not api_app.save():
            self.add_errors(api_app.errors)
            return self.render('developers/edit-app.html', app=api_app)
            
        return self.redirect("/developers/view-app/%s" % (api_app.id))
