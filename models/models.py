from odoo import api, fields, models
from odoo.exceptions import ValidationError
from random import randint
from datetime import timedelta, datetime, date

class TrainingCourse(models.Model):
    _name = 'training.course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Training Course'

    def get_default_color(self):
            return randint(1, 11)

    name = fields.Char(string='Judul', required=True, tracking=True)
    description = fields.Text(string='Keterangan', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Penanggung Jawab', tracking=True)
    session_line = fields.One2many('training.session', 'course_id', string="Sesi Pelatihan", tracking=True)
    product_ids = fields.Many2many('product.product', 'course_product_rel', 'course_id', 'product_id', 'Cendera Mata', tracking=True)
    ref = fields.Char(string='Referensi', readonly=True, default='/')
    level = fields.Selection([('basic', 'Dasar'), ('advanced', 'Lanjutan')], string='Tingkatan', default='basic')
    color = fields.Integer('Warna', default=get_default_color)
    email = fields.Char(string="Email", related='user_id.login')

    sql_constraints = [
        ('nama_kursus_unik', 'UNIQUE(name)', 'Judul kursus harus unik'),
        ('nama_keterangan_cek', 'CHECK(name != description)', 'Judul kursus dan keterangan tidak boleh sama ')
    ]

    def copy(self, dafault=None):
        default = dict(dafault or {})
        default.update(name=("%s (copy)" % self.name or ''))
        return super(TrainingCourse, self).copy(default)
    
    
 
    @api.model
    def create(self, vals):
        vals['ref'] = self.env['ir.sequence'].next_by_code('training.course')
        return super(TrainingCourse, self).create(vals)
 

class TrainingSession(models.Model):
    _name = 'training.session'
    _description = 'Training Session'

    course_id = fields.Many2one('training.course', string='Judul Kursus', required=True, ondelete='cascade')
    name = fields.Char(string='Nama', required=True)
    start_date = fields.Date(string='Tanggal', default=fields.Date.context_today)
    duration = fields.Float(string='Durasi', help="Jumlah Hari Training", default=3)
    seats = fields.Integer(string='Kursi', help="Jumlah Kuota Kursi", default=10)
    partner_id = fields.Many2one('res.partner', string='Instruktur', domain=[('instructor', '=', True), ('category_id', 'ilike', 'Pengajar')])
    attendee_ids = fields.Many2many('training.attendee', 'session_attendee_rel', 'session_id', 'attendee_id', 'Peserta')
    taken_seats = fields.Integer(string="Kursi Terisi", compute='compute_taken_seats')


    @api.depends('seats', 'attendee_ids')
    def compute_taken_seats(self):
        for sesi in self:
            sesi.taken_seats = 0
            if sesi.seats and sesi.attendee_ids:
                sesi.taken_seats = 100 * len(sesi.attendee_ids) / sesi.seats

    
    @api.constrains('seats', 'attendee_ids')
    def check_seats_and_attendees(self):
        for r in self:
            if r.seats and len(r.attendee_ids) > r.seats:
                raise ValidationError('Kuota kursi tidak mencukupi')

    @api.onchange('duration')
    def verivy_valid_duration(self):
        if self.duration <=0:
            self.duration = 1
            return {
                'warning':{
                    'title': 'Perhatian',
                    'message': 'Durasi harus lebih dari 0'
                }
            }

    @api.depends('start_date', 'duration')
    def get_end_date(self):
        for sesi in self:
            if not sesi.start_date: 
                sesi.end_date = sesi.start_date
                continue
 
            start = fields.Date.from_string(sesi.start_date)
            sesi.end_date = start + timedelta(days=sesi.duration)
         
    def set_end_date(self):
        for sesi in self:
            if not (sesi.start_date and sesi.end_date):
                continue
             
            start_date = fields.Datetime.from_string(sesi.start_date)
            end_date = fields.Datetime.from_string(sesi.end_date)
            sesi.duration = (end_date - start_date).days + 1
 
    ...
    ...
     
    end_date = fields.Date(string="Tanggal Selesai", compute='get_end_date', inverse='set_end_date', store=True)
    attendees_count = fields.Integer(string="Jumlah Peserta", compute='get_attendees_count', store=True)
  
    @api.depends('attendee_ids')
    def get_attendees_count(self):
        for sesi in self:
            sesi.attendees_count = len(sesi.attendee_ids)                          


class TrainingAttendee(models.Model):
    _name ='training.attendee'
    _description = 'Training Peserta'
    _inherits ={'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', 'Partner', required=True, ondelete='cascade')
    name = fields.Char(related='partner_id.name', inherited=True, readonly=False)
    session_ids = fields.Many2many('training.session', 'session_attendee_rel', 'attendee_id', 'session_id', 'Sesi')
    sex = fields.Selection([
        ('male', 'Laki-Laki'),
        ('female', 'Perempuan')
    ], string='Jenis Kelamin', required=True, help="Pilih Jenis Kelamin")

    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Menikah'),
        ('divorced', 'Cerai')
    ], string='Status Perkawinan')
