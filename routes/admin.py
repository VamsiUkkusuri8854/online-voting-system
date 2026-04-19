import time
import logging
from flask import Blueprint, request, jsonify
from database import get_db
from bson.objectid import ObjectId
from utils.auth_middleware import admin_required
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/voting-toggle', methods=['POST'])
@admin_required
def voting_toggle(current_user):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
    
    data = request.json
    action = data.get('action') # "start" or "stop"
    duration = data.get('duration', 0) # minutes
    
    settings = db["settings"]
    
    if action == "start":
        end_time = datetime.utcnow() + timedelta(minutes=int(duration))
        settings.update_one({}, {
            '$set': {
                'voting_active': True,
                'end_time': end_time.isoformat()
            }
        }, upsert=True)
        return jsonify({'message': 'Voting started successfully!'}), 200
    else:
        settings.update_one({}, {
            '$set': {
                'voting_active': False,
                'end_time': None
            }
        }, upsert=True)
        return jsonify({'message': 'Voting stopped successfully!'}), 200

def get_candidates_collection():
    db = get_db()
    return db["candidates"] if db is not None else None

@admin_bp.route('/admin/add-candidate', methods=['POST'])
@admin_required
def add_candidate(current_user):
    candidates_coll = get_candidates_collection()
    if candidates_coll is None:
        return jsonify({'message': 'Database connection error!'}), 503

    start_time = time.perf_counter()
    data = request.json
    name = data.get('name')
    party = data.get('party')

    if not all([name, party]):
        return jsonify({'message': 'Name and party are required!'}), 400

    candidate_id = candidates_coll.insert_one({
        'name': name,
        'party': party,
        'votes': 0
    }).inserted_id

    elapsed = (time.perf_counter() - start_time) * 1000
    logging.info(f"ADMIN_ADD_CANDIDATE: {elapsed:.2f}ms")

    return jsonify({'message': f'Candidate {name} added successfully!', 'id': str(candidate_id)}), 201

@admin_bp.route('/admin/delete_candidate/<candidate_id>', methods=['DELETE'])
@admin_required
def delete_candidate(current_user, candidate_id):
    db = get_db()
    candidates_coll = db["candidates"] if db is not None else None
    if candidates_coll is None:
        return jsonify({'message': 'Database connection error!'}), 503

    start_time = time.perf_counter()
    # Delete related votes from "votes" collection if it exists
    if db is not None:
        db["votes"].delete_many({"candidate_id": ObjectId(candidate_id)})
        
    result = candidates_coll.delete_one({'_id': ObjectId(candidate_id)})
    
    elapsed = (time.perf_counter() - start_time) * 1000
    logging.info(f"ADMIN_DELETE_CANDIDATE: {elapsed:.2f}ms")
    
    if result.deleted_count == 0:
        return jsonify({'message': 'Candidate not found!'}), 404
    return jsonify({'message': 'Candidate deleted successfully!'}), 200

@admin_bp.route('/admin/update_candidate/<candidate_id>', methods=['PUT', 'POST'])
@admin_required
def update_candidate(current_user, candidate_id):
    candidates_coll = get_candidates_collection()
    if candidates_coll is None:
        return jsonify({'message': 'Database connection error!'}), 503

    start_time = time.perf_counter()
    data = request.json
    name = data.get('name')
    party = data.get('party')

    if not all([name, party]):
        return jsonify({'message': 'Name and party are required!'}), 400

    result = candidates_coll.update_one(
        {'_id': ObjectId(candidate_id)},
        {'$set': {'name': name, 'party': party}}
    )

    elapsed = (time.perf_counter() - start_time) * 1000
    logging.info(f"ADMIN_EDIT_CANDIDATE: {elapsed:.2f}ms")

    if result.matched_count == 0:
        return jsonify({'message': 'Candidate not found!'}), 404

    return jsonify({'message': 'Candidate updated successfully!'}), 200

@admin_bp.route('/admin/requests', methods=['GET'])
@admin_required
def get_admin_requests(current_user):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
    
    # Fetch all pending requests
    requests_list = list(db["candidate_requests"].find({'status': 'pending'}))
    for r in requests_list:
        r['id'] = str(r['_id'])
        del r['_id']
        if 'user_id' in r:
            r['user_id'] = str(r['user_id'])
        
    return jsonify(requests_list), 200

@admin_bp.route('/admin/approve_request/<request_id>', methods=['POST'])
@admin_required
def approve_candidate_request(current_user, request_id):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
        
    request_doc = db["candidate_requests"].find_one({'_id': ObjectId(request_id)})
    if not request_doc:
        return jsonify({'message': 'Request not found!'}), 404
        
    if request_doc['status'] != 'pending':
        return jsonify({'message': 'Only pending requests can be approved!'}), 400

    start_time = time.perf_counter()
    
    # 1. Update request status
    db["candidate_requests"].update_one(
        {'_id': ObjectId(request_id)},
        {'$set': {'status': 'approved'}}
    )
    
    # 2. Add to actual candidates collection
    db["candidates"].insert_one({
        'name': request_doc['name'],
        'party': request_doc['party'],
        'votes': 0
    })
    
    elapsed = (time.perf_counter() - start_time) * 1000
    logging.info(f"ADMIN_APPROVE_CANDIDATE: {elapsed:.2f}ms")
    
    return jsonify({'message': 'Request approved and candidate added!'}), 200

@admin_bp.route('/admin/reject_request/<request_id>', methods=['POST'])
@admin_required
def reject_candidate_request(current_user, request_id):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
        
    result = db["candidate_requests"].update_one(
        {'_id': ObjectId(request_id), 'status': 'pending'},
        {'$set': {'status': 'rejected'}}
    )
    
    if result.matched_count == 0:
        return jsonify({'message': 'Pending request not found!'}), 404
        
    return jsonify({'message': 'Request rejected successfully!'}), 200

@admin_bp.route('/admin/stats', methods=['GET'])
@admin_required
def get_admin_stats(current_user):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
    
    candidates = list(db["candidates"].find({}, {'name': 1, 'votes': 1}))
    total_votes = sum(c['votes'] for c in candidates)
    
    leader = "None"
    max_votes = -1
    
    if candidates:
        leader_doc = max(candidates, key=lambda x: x['votes'])
        if leader_doc['votes'] > 0:
            leader = leader_doc['name']
            max_votes = leader_doc['votes']

    # New: Count total registered users
    total_users = db["users"].count_documents({})
    
    return jsonify({
        'total_votes': total_votes,
        'leader': leader,
        'leader_votes': max_votes,
        'total_users': total_users,
        'participation_rate': round((total_votes / total_users * 100), 2) if total_users > 0 else 0
    }), 200
