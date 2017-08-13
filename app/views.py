import json
import random
import datetime
import threading
import time
import traceback

from flask import redirect, render_template
from flask.ext.classy import FlaskView, route
import inflect

from app import app, db
from app.models import * 
from app.forms import SimpleMturkForm
from mturk import grant_qualification
from mturk import manage_hits
import config


# inflect_eng = inflect.engine()
# _quiz_threshold = 0.8

@app.route('/')
@app.route('/index')
def index():
    return "Welcome to sample flask_mturk website!"


class WorkerView(FlaskView):
    def index(self):        
        return "Worker"

    @route('/<int:id>/') 
    def get(self, id):
        print time_stamp(str(id))
        stmt = 'select count(*) from annotation where worker_id = %s' % (str(id))
        ann_cnt = get_first_db_res(stmt)
        if ann_cnt == None:
            ann_cnt = 0            
        return "Worker %d has %d annotations" % (id, ann_cnt)

WorkerView.register(app)

class AnnView(FlaskView):
    def index(self):
        print time_stamp('ann')
        stmt = 'select count(*) from annotation'
        ann_cnt = get_first_db_res(stmt)
        print ann_cnt
        return "There are %d annotations in the database" % (ann_cnt)

    @route('/<int:id>/') 
    def get(self, id):
        print time_stamp('Annotation: '+str(id))

        ann = Annotation.query.get(id)

        print ann
        return render_template('ann.html', 
                               title = 'Annotation',
                               ann = ann)


AnnView.register(app)

class TaskView(FlaskView):
    def index(self):
        return "Task"

    @route('/<int:id>/', methods=['GET']) 
    def get(self, id):
        '''
        HIT task, detailed in Job with id = < id >
        '''
        try:
            print time_stamp('Annotation Task for Job: '+str(id))
            job = Jobs.query.get(id)        
            cmd = json.loads(job.cmd)
            label = cmd['label']
            if 'categories' in label:
                label = label.split(' ')[0]
                label_heading = 'Categories'
            else:
                label_heading = 'Attributes'
            label_title = inflect_eng.plural(label).title()
            patches = cmd['patches']
            attributes = cmd['attributes']
            for item in attributes:
                item['defn'] = Label.query.get(item['id']).defn

            # Make form
            form = AnnForm()
            
            # outline the objects or not
            use_outline = 0 if label == 'scene' else 1


            return render_template('annotate.html', 
                                   title = 'Annotate '+label_heading, 
                                   label = label, 
                                   label_title = label_title,
                                   label_heading = label_heading,
                                   attributes = attributes,
                                   patches = patches, 
                                   use_outline = use_outline,
                                   form = form)
        except KeyError, e:
            # if this is an all images hit instead of an exhaustive hit
            return self.get_all_imgs(id)

    @route('/<int:id>/', methods=['POST']) 
    def post(self, id):
        print '**** in post ****'         
        form = AnnForm()
        print id
        if form.validate_on_submit():
            hit_id = get_form_details(form, id)
            print hit_id
            # add_attribute_annotations(json.loads(form.resp.data), hit_id, id)
            t = threading.Thread(target=add_attribute_annotations, args=(json.loads(form.resp.data), hit_id, id))
            t.start()
        else:
            print 'did not validate'
            print form.errors
        return self.get(id)


    @route('/hit/<int:id>/', methods=['GET']) 
    def get_hit_replay(self, id):
        '''
        Replay HIT for attribute annotation task, associated with hit_response id of <id> 
        '''
        print time_stamp('HIT Replay: '+str(id))
        jid = get_all_db_res("select count(*) as c, job_id from hit_details where hits like '%%"+str(id)+"%%' group by job_id order by c desc")
        print ' number of annotations | job_id assoc. with hit id '
        print jid
        jid = jid[0][1]
        job = Jobs.query.get(jid)
        cmd = json.loads(job.cmd)
        label = cmd['label']
        if 'categories' in label:
            label = label.split(' ')[0]
            label_heading = 'Categories'
        else:
            label_heading = 'Attributes'
        label_title = inflect_eng.plural(label).title()
        patches = cmd['patches']
        attributes = cmd['attributes']
        for item in attributes:
            item['defn'] = Label.query.get(item['id']).defn

        # Make form
        form = AnnForm()
        
        # outline the objects or not
        use_outline = 0 if label == 'scene' else 1

        # annotations
        annotations = []
        for patch in patches:
            cur_anns = []
            for attr in attributes:
                try:
                    val = Annotation.query.filter(Annotation.hit_id == id).filter(Annotation.patch_id == patch['id']).filter(Annotation.label_id == attr['id']).first().value
                    val = 1 if val else 0
                except Error, e:
                    print e
                print val
                cur_anns.append(val)
            annotations.append(cur_anns)
        print annotations

        return render_template('annotate.html', 
                               title = 'Annotate '+label_heading, 
                               label = label, 
                               label_title = label_title,
                               label_heading = label_heading,
                               attributes = attributes,
                               patches = patches, 
                               use_outline = use_outline,
                               form = form, 
                               is_replay = True, 
                               annotations = annotations)



    @route('/quiz/<int:id>/', methods=['GET']) 
    def quiz(self, id):
        print time_stamp('Quiz Task for Job: '+str(id))
        job = Jobs.query.get(id)        
        cmd = json.loads(job.cmd)
        label = cmd['label']
        if 'categories' in label:
            label = label.split(' ')[0]
            label_heading = 'Categories'
        else:
            label_heading = 'Attributes'
        label_title = inflect_eng.plural(label).title()
        patches = cmd['patches']
        attributes = cmd['attributes']
        for item in attributes:
            item['defn'] = Label.query.get(item['id']).defn
        answers = cmd['answers']
        print answers
        try:
            alt_answers = cmd['alt_answers']
            print alt_answers
        except KeyError, e:
            alt_answers = answers
        # Make form
        form = AnnForm()
        
        # outline the objects or not
        use_outline = 0 if label == 'scene' else 1

        return render_template('quiz.html', 
                               title = 'Annotation Quiz', 
                               label = label, 
                               label_title = label_title,
                               label_heading = label_heading,
                               attributes = attributes,
                               patches = patches, 
                               use_outline = use_outline,
                               answers = answers,
                               alt_answers = alt_answers,
                               form = form)

    @route('/quiz/<int:id>/', methods=['POST']) 
    def quiz_post(self, id):
        print '****** in quiz/ post ******'        
        form = AnnForm()
        print '** quiz id : %d **' % id
        if form.validate_on_submit():
            worker_id = get_form_details(form, id, return_worker=True)
            add_worker_quiz_score(json.loads(form.resp.data), worker_id, id)
        else:
            print 'did not validate'
            print form.errors
        return self.get(id)




TaskView.register(app)

class LabelView(FlaskView):

    def index(self):
        print time_stamp('label')
        stmt = 'select * from label'
        lbls = get_all_db_res(stmt)

        return "There are %d labels in the database: %s" % (len(lbls), str(lbls))

    @route('/<int:id>/', methods=['GET'])
    @route('/<int:id>/<int:cat>/', methods=['GET'])
    @route('/<int:id>/<int:cat>/<int:uo>/', methods=['GET'])
    def get_labeled_imgs(self, id, cat=[], uo=0):
        '''
        print out all images with a positive consensus labels for label_id == id
        '''
        print '***** Getting positve patches for label_id %d *****' % id
        if cat != []:
            label = Label.query.get(cat).name
        else:
            label = 'all categories'
        print '**** '+label
        pids = manage_hits.find_positives([id], [], cat)[:200]
        label_heading = 'Attributes'
        label_title = label
        patches = []
        for patch_id in pids:
            p = Patch.query.get(patch_id)
            seg = [json.loads(p.segmentation)[0]]
            segx = [seg[0][ix] for ix in range(0,len(seg[0]),2)]
            segy = [seg[0][iy] for iy in range(1,len(seg[0]),2)]
            img_id = p.image_id
            seg.append(p.x) 
            seg.append(p.y)
            seg.append(p.width)
            seg.append(p.height)
            img = Image.query.get(img_id)
            seg.append(img.width)
            seg.append(img.height)
            patches.append({'id': patch_id, 'image_id': img_id, 'segmentation': json.dumps(seg)})

        attribute = {}
        attribute['id'] = id
        attribute['name'] = Label.query.get(id).name
        attribute['defn'] = Label.query.get(id).defn

        print patches
        print attribute

        # Make form
        form = AnnForm()

        # outline the objects or not
        use_outline = uo #0 if label == 'scene' else 1
        print '***** Rendering positve patches for label_id %d *****' % id
        return render_template('annotate_all_imgs.html',
                               title = 'Annotate '+label_heading,
                               label = label,
                               label_title = label_title,
                               attribute = attribute,
                               patches = patches,
                               use_outline = use_outline,
                               form = form)


def get_form_details(form, job_id, return_worker=False):

    if form.worker.data.startswith('mturk_'):
        employer = 1
        username = form.worker.data.replace('mturk_', '')
    else:
        employer = 2
        username = form.worker.data
    worker = Worker.query.filter_by(username = username).first()

    if not worker:
        # check if worker is from mturk
        app.logger.info('New Worker: '+username)
        worker = Worker(username = username, quiz_score = 0.0, employer_id = employer, password = '')
        db.session.add(worker)
        worker.location = form.location.data
        worker.nationality = form.nationality.data

    print '.......making hit.......'
    print 'form.assignment_id.data ' + str(form.assignment_id.data)
    print 'form.hit_id.data ' +str(form.hit_id.data)
    hit_resp = HitResponse(time = form.time.data, 
                           worker = worker, 
                           assignment_id = form.assignment_id.data, 
                           mturk_hit_id = form.hit_id.data,
                           job_id = job_id)
    db.session.add(hit_resp)
    db.session.commit()

    hit_id = hit_resp.id
    print 'hit_id '+str(hit_id)
    print time_stamp('Added hit details')

    # hits_done_by_worker = get_first_db_res('select count(*) from hit_response where worker_id = %d' % worker.id)
    # if hits_done_by_worker > worker.ok_until:
    #     sbj = "[cocottributes] worker %d over hit number limit %d/%d " % (worker.id, hits_done_by_worker, worker.ok_until)
    #     email_notify(message='', subject=sbj, to_addr=config.notify_addr)
    # else:
    #     print "Worker %d under hit number limit %d/%d " % (worker.id, hits_done_by_worker, worker.ok_until)
    
    if return_worker:
        return worker.id

    return hit_id

def add_attribute_annotations(data, hit_id, job_id):
    '''
    Takes list of attribute annotations, format:  [{ image_id: xxx, patch_id: xxx, label_id: xxx, value: t/f }, ... ]
    Adds annotations to annotations table with reference to corresponding hit_id
    '''
    print 'adding annotation'
    print 'adding annotation hit_id: '+str(hit_id)
    # print data
    print 'number of annotations from this hit (should be 200): %d' % len(data)
    # todo: make this one insert statement
    stmt = 'insert into annotation (value, patch_id, image_id, label_id, hit_id) values'
    rows = []
    for item in data:
        # add annotation row
        rows.append('(%r, %d, %d, %d, %d)' % (item["value"], item["patch_id"], item["image_id"], item["label_id"], hit_id))

        hd = HitDetails.query.filter(HitDetails.image_id == item["image_id"]).filter(HitDetails.patch_id == item["patch_id"]).filter(HitDetails.label_id == item["label_id"]).filter(HitDetails.job_id == job_id).first()
        if hd:
            if hd.hits:
                hd.hits = ', '.join([hd.hits, str(hit_id)])
            else:
                hd.hits = str(hit_id)
            hd.num_hits = hd.num_hits + 1
    stmt += ', '.join(rows)
    db.engine.execute(stmt)
    db.session.commit()
                
    print '*** num active threads %s ***' % str(threading.active_count())
    return True

def add_worker_quiz_score(score, worker_id, job_id):
    print '**** Add quiz score ****'
    print score
    print worker_id
    print job_id
    q = Quiz(score=score, job_id=job_id, worker_id=worker_id)
    db.session.add(q)
    db.session.commit()

    if data[0] >= _quiz_threshold:
        qualid = HitQualification.query.filter(HitQualification.job_id==job_id).first().qualtypeid
        worker_name = Worker.query.get(worker_id).username
        print qualid
        print worker_name
        grant_qualification.grant_qual(qualid, worker_name)
        print '**** Granted Qualification %s to worker %s ****' % (qualid, worker_name)


def get_first_db_res(stmt):
    try:
        return db.engine.execute(stmt).fetchall()[0][0]
    except IndexError, e:
        return None

def get_all_db_res(stmt):
    return db.engine.execute(stmt).fetchall()

def time_stamp(print_str):
    ts = str(datetime.datetime.now())
    print '%s -- %s' % (ts, print_str)
    return 

def email_notify(message, subject, to_addr):
    output = subprocess.check_output("echo '%s' | mail -s '%s' %s" % (message, subject, to_addr), shell=True)
    return output
