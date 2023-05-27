import os
from datetime import datetime
import pytz
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

seoul_tz = pytz.timezone('Asia/Seoul')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey1232'
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)

# 게시글
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    author = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<Post %r>' % self.title
    
class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')
    author = StringField('Author', validators=[DataRequired()])

#댓글
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author = db.Column(db.String(100), nullable=False)

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')
    author = StringField('Author', validators=[DataRequired()])



@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)



@app.route('/create', methods=['GET', 'POST'])
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = post = Post(title=form.title.data, content=form.content.data, author=form.author.data, timestamp=datetime.now(seoul_tz))

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_post.html', form=form)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    form = CommentForm()

    if form.validate_on_submit():
        comment = comment = Comment(content=form.content.data, author=form.author.data, post_id=post.id, timestamp=datetime.now(seoul_tz))

        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added.', 'success')
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('post_detail.html', post=post, comments=comments, form=form)


@app.route('/post/<int:post_id>/comment', methods=['GET', 'POST'])
def comment_post(post_id):
    form = CommentForm()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=form.author.data, post_id=post.id, timestamp=datetime.now(seoul_tz))
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added.', 'success')
        return redirect(url_for('post_detail', post_id=post_id))
    return render_template('comment_post.html', title='New Comment', form=form)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run()
