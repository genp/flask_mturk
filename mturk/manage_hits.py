import json
import os
import subprocess

import numpy as np
import shutil

import config
from app import app, db
from app.models import * 

def get_recent_job_types(interval):
    '''
    interval is a string, e.g. '1 month' or '12 hours'
    '''
    job_types = [x[0] for x in db.engine.execute("select distinct job_type, max(start_time) from jobs where start_time > current_timestamp - interval '%s' group by job_type order by max(start_time) desc" % interval).fetchall()]

    return job_types

# finds whole hits that need to be repeated
def get_missing_hits(job_type):
    '''
    returns list of job_ids that have less than 3 hits by trusted workers
    job_id occur multiple times if missing multiple hits
    '''
    stmt = "select id, cnt from (select j.id, count(*) as cnt from jobs j, hit_response h where h.job_id = j.id and j.job_type = '%s' group by j.id) as hit_cnt where cnt < 3" % job_type    
    job_cnt = db.engine.execute(stmt).fetchall()

    jobs_to_print = []

    for item in job_cnt:
        for cnt in range(int(item[1])):
            jobs_to_print.append(item[0])

    return jobs_to_print

def launch_missing_hits(job_type, task_file, mturk_rel_path):
    jobs = get_missing_hits(job_type)
    return launch_hits(jobs, task_file, mturk_rel_path)
    

def launch_hits(jobs, task_file, mturk_rel_path):
    '''
    list of jobs to be launched on mturk
    task_file to write jobs to
    mturk_rel_path - task dir argument to run.sh
    '''
    f = open(task_file, 'w')
    f.writelines('job_id\n')
    f.write('\n'.join([str(x) for x in jobs]))
    f.close()
    cwd = os.getcwd()
    os.chdir(config.mturk_bin_path)
    output = subprocess.check_output("./run.sh %s" % (mturk_rel_path), shell=True)
    # appends hit ids to long running file
    os.system("touch %s" % task_file.replace('input', 'success_all'))
    output = subprocess.check_output("cat %s >> %s" % (task_file.replace('input', 'success'), task_file.replace('input', 'success_all')), 
                                     shell=True)
    os.chdir(cwd)
    return output


