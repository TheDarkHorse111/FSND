import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random
from sqlalchemy.orm import query

from sqlalchemy.sql.expression import true

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
#method to paginate 10 questions per page
def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  #enable CORS
  CORS(app, resource={r"*/*" : {"origins": '*'}})
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  #set Access-Control-Allow for headers and methods
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers','Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods','GET, POST, DELETE, OPTION')
    return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  #endpoint and method to get all categories
  @app.route('/categories')
  def get_categories():
    categories = Category.query.order_by(Category.id).all()
    cates = {}
    for cate in categories:
      temp = cate.format()
      cates.update({cate.id:cate.type})
    if len(categories) == 0:
      abort(404)
    return jsonify({
      'success': True,
      'categories':cates
      })

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  #endpoint and method to get all questions 
  @app.route('/questions')
  def get_questions():
    selection = Question.query.order_by(Question.id).all()
    categories = Category.query.order_by(Category.id).all()
    cates = {}
    current_questions = paginate_questions(request,selection)
    for cate in categories:
      temp = cate.format()
      cates.update({cate.id:cate.type})
    if len(current_questions) == 0:
      abort(404)
      
    return jsonify({
      "success": True,
      "questions": current_questions,
      "total_questions": len(Question.query.all()),
      "categories": cates,
      "current_category":None
    })

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  #endpoint and method to delete a question
  @app.route('/questions/<int:question_id>',methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()
      if question is None:
        abort(404)
      question.delete()

      return jsonify({
        "success":True,
        "deleted":question_id
      })
    except:
      abort(422)
  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  #endpoint and method to post a new question as well as to search for quastions depending on the search term
  @app.route('/questions', methods=['POST'])
  def insert_or_search_question():
    body = request.get_json()

    search_term = body.get('searchTerm', None)
    
    if search_term is None:
      new_question = body.get('question', None)
      new_answer = body.get('answer', None)
      new_category = body.get('category', None)
      new_difficulty = int(body.get('difficulty', None))
      try:
        question = Question(question=new_question,answer=new_answer,category=new_category,difficulty=new_difficulty)
        question.insert()
        return jsonify({
          'success':True
        })
      except:
        abort(422)
    else:
      searched_questions = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
      current_questions = paginate_questions(request,searched_questions)

      return jsonify({
        'success':True,
        'questions':current_questions,
        'total_questions':len(Question.query.all()),
        'current_category':None
      })
  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
 
  #solved at the /questions POST request 
    
  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  #endpoint and method to get questions based on a certain category
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
    questions = Question.query.order_by(Question.id).filter(Question.category==category_id).all()
    category = Category.query.filter(Category.id == category_id).one_or_none()
    current_questions = paginate_questions(request, questions)

    if len(current_questions) == 0:
      abort(404)
    
    if category is None:
      abort(404)
      
    return jsonify({
      "success": True,
      "questions": current_questions,
      "total_questions": len(Question.query.all()),
      "current_category":category.type
    })


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  #endpoint and method to start the quiz
  @app.route('/quizzes', methods=['POST'])
  def start_quiz():
    body = request.get_json()

    previous_questions = body.get('previous_questions', None)
    quiz_category = body.get('quiz_category', None)

    if ((quiz_category is None) or (previous_questions is None)):
      abort(400)

    #get a certain category question or get all questions depending on the quiz category id 
    if quiz_category['id'] == 0:
      questions = Question.query.order_by(Question.id).all()
    else:
      category = Category.query.filter(Category.id == quiz_category['id']).first()
      questions = Question.query.filter(Question.category == category.id).all()
    
    
    #format questions
    questions_list = [question.format() for question in questions]

    #method to get a random question
    def get_rand_question(questions):
      return questions[random.randint(0,len(questions)-1)]
    question = get_rand_question(questions_list)

    #if question was picked then get another question that wasn't picked
    while question["id"] in previous_questions:
      question = get_rand_question(questions_list)
    
    #send only a success message if all questions were consumed otherwise send a new question
    if len(previous_questions) >= len(questions):
      return jsonify({
        "success":True
      }) 
    else:
      return jsonify({
        "success": True,
        "question" : question
      })
    



  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  #error handling section
  
  @app.errorhandler(404)
  def not_found(error):
      return (
          jsonify({"success": False, "error": 404, "message": "resource not found"}),
          404,
      )

  @app.errorhandler(422)
  def unprocessable(error):
      return (
          jsonify({"success": False, "error": 422, "message": "unprocessable"}),
          422,
      )

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

  @app.errorhandler(405)
  def not_allowed(error):
      return (
          jsonify({"success": False, "error": 405, "message": "method not allowed"}),
          405,
      )
  
  @app.errorhandler(500)
  def server_error(error):
      return (
          jsonify({"success": False, "error": 500, "message": "internal server error"}),
          500,
      )
  return app

    