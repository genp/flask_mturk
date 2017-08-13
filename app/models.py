from app import db

class Worker(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  username = db.Column(db.String(), index = True, unique = True)
  password = db.Column(db.String(), nullable = False)
  email = db.Column(db.String(120), index=True, unique=True)
  # score on instructional quiz
  quiz_score = db.Column(db.Float(), index = True)
  employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'))
  employer = db.relationship('Employer', backref = db.backref('workers', lazy = 'dynamic'))

  age = db.Column(db.Integer)
  gender = db.Column(db.String())
  education = db.Column(db.String())
  # this is physical location
  location = db.Column(db.String())
  nationality = db.Column(db.String())
  income = db.Column(db.String())
  is_blocked = db.Column(db.Boolean(), default=False)
  on_probation = db.Column(db.Boolean(), default=False)
  ok_until = db.Column(db.Integer, default=30) # stores a number of HITs this worker is approved to do  
  
  def is_authenticated(self):
    return True

  def is_active(self):
    return True

  def is_anonymous(self):
    return False

  def get_id(self):
    return unicode(self.id)

  def __repr__(self):
    return str(self.__dict__)

class Employer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

    def __repr__(self):
        return '<Employer %r>' % (self.name)


class Word(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String())

  parent_id = db.Column(db.Integer, db.ForeignKey('word.id'), index = True)


  hit_id = db.Column(db.Integer, db.ForeignKey('hit_response.id'))
  hit = db.relationship('HitResponse', backref = db.backref('words', lazy = 'dynamic'))

  def url(self):
    return "/word/"+self.name

  def __repr__(self):
    return str(self.__dict__)



class Annotation(db.Model):
  id = db.Column(db.BigInteger, primary_key = True)
  value = db.Column(db.Boolean(), nullable=False)
  timestamp = db.Column(db.DateTime(), default=db.func.now())


  word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
  word = db.relationship('Word', backref = db.backref('annotations', lazy = 'dynamic'))

  hit_id = db.Column(db.Integer, db.ForeignKey('hit_response.id'), nullable=False)
  hit = db.relationship('HitResponse', backref = db.backref('annotations', lazy = 'dynamic'))

  def __repr__(self):
    return str(self.__dict__)

class Jobs(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  cmd = db.Column(db.String(), nullable=False)
  start_time = db.Column(db.DateTime(), default=db.func.now())
  end_time = db.Column(db.DateTime())
  isrunning = db.Column(db.Boolean(), index=True)
  # this is for expected time - 'short', 'long', 'vlong'
  job_type = db.Column(db.String())
  
  def __repr__(self):
    return str(self.__dict__)
  
class Quiz(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  submit_time = db.Column(db.DateTime(), default=db.func.now())
  tp = db.Column(db.Float())
  fp = db.Column(db.Float())
  tn = db.Column(db.Float())
  fn = db.Column(db.Float())
  
  # the user that submitted this quiz
  worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'),  nullable=False)
  worker = db.relationship('Worker', backref = db.backref('quizes', lazy = 'dynamic'))  

  # the job associated with this quiz
  job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'),  nullable=False)
  job = db.relationship('Jobs', backref = db.backref('quizes', lazy = 'dynamic'))  

  def __repr__(self):
    return str(self.__dict__)

class HitResponse(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  # the completion time for all of the patch responses associated with this HIT
  time = db.Column(db.Float(), nullable=False)
  timestamp = db.Column(db.DateTime(), default=db.func.now())
  # the confidence of the labeling user

  score = db.Column(db.String())
  assignment_id = db.Column(db.String())
  mturk_hit_id = db.Column(db.String())

  # the user that submitted this hit
  worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'),  nullable=False)
  worker = db.relationship('Worker', backref = db.backref('hits', lazy = 'dynamic'))

  # the job that this hit is associated with
  job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'),  nullable=False)
  job = db.relationship('Jobs', backref = db.backref('hits', lazy = 'dynamic'))

  def __repr__(self):
    return str(self.__dict__)

class HitQualification(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  qualtypeid = db.Column(db.String())

  # the job associated with this MTurk Qualification
  job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
  job = db.relationship('Jobs', backref = db.backref('hit_quals', lazy = 'dynamic'))  

  def __repr__(self):
    return str(self.__dict__)

