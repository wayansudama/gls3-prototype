from odoo.tools.misc import get_lang
from odoo import _, api, fields, models
from odoo.tools.float_utils import float_round

class CostSheet(models.Model):
    _name = 'cost.sheet'
    _description = 'Cost Sheet'
    _inherit = ['portal.mixin','mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Name',tracking=True)
    crm_id = fields.Many2one('crm.lead', string='CRM',tracking=True,copy=True)
    partner_id = fields.Many2one('res.partner', string='Customer',copy=True)
    date_document = fields.Date('Request Date',tracking=True,default=fields.Date.today)
    user_id = fields.Many2one('res.users', string='Responsible',default=lambda self:self.env.user.id)
    rab_template_id = fields.Many2one('rab.template', string='RAB Template',tracking=True,copy=True)
    note = fields.Text('Term and condition',copy=True)
    tax_ids = fields.Many2many('account.tax', string='Taxs',copy=True)
    tax_id = fields.Many2one('account.tax', string='Tax',copy=True)
    rev = fields.Integer('Revision')
    revisied = fields.Boolean('Revisied')
    cost_sheet_revision_id = fields.Many2one('cost.sheet', string='Cost Sheet Revision')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submited'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
    ], string='Status',tracking=True, default="draft")
    # margin_type = fields.Selection([
    #     ('percentage', 'Percentage'),
    #     ('amount', 'Amount'),
    # ], string='Margin Type',default='percentage')
    # margin_amount_input = fields.Monetary('Margin Amount')
    # margin_percent_input = fields.Float('Margin %')
    
    line_ids = fields.One2many('project.rab', 'cost_sheet_id', string='RAB.')  
    rab_line_ids = fields.One2many('rab.line', 'cost_sheet_id', string='RAB',copy=True)
    general_work_line_ids = fields.One2many('general.work', 'cost_sheet_id', string='General Work',copy=True)
    intake_package_line_ids = fields.One2many('intake.package', 'cost_sheet_id', string='Intake Package',copy=True)
    pretreatment_package_line_ids = fields.One2many('pretreatment.package', 'cost_sheet_id', string='Pretreatment Package',copy=True)
    swro_package_line_ids = fields.One2many('swro.package', 'cost_sheet_id', string='SWRO Package',copy=True)
    brine_injection_package_line_ids = fields.One2many('brine.injection.package', 'cost_sheet_id', string='Brine Injection Package',copy=True)
    product_package_line_ids = fields.One2many('product.package', 'cost_sheet_id', string='Product Package',copy=True)
    electrical_package_line_ids = fields.One2many('electrical.package', 'cost_sheet_id', string='Electrical Package',copy=True)
    civil_work_line_ids = fields.One2many('civil.work', 'cost_sheet_id', string='Civil Work',copy=True)
    ga_project_line_ids = fields.One2many('ga.project', 'cost_sheet_id',copy=True)
    waranty_line_ids = fields.One2many('waranty.waranty', 'cost_sheet_id',copy=True)
      
    

    # purchase_id = fields.Many2one('purchase.requisition', string='Purchase')

    # total_margin = fields.Float(compute='_compute_total_amount', string='Total Margin',store=True)
    # total_without_margin = fields.Float(compute='_compute_total_amount', string='Price Subtotal',store=True)
    ga_project = fields.Float('GA Project',compute="_compute_ga_project",store=True,copy=True)
    ga_project_percent = fields.Float('GA Project Percent',compute="_compute_ga_project",store=True,copy=True)
    project_hse = fields.Float('Project HSE',compute="_compute_project_hse",store=True,copy=True)
    project_hse_percent = fields.Float('Project HSE Percent',copy=True)
    car = fields.Float('Construction All Risk',compute="_compute_car",store=True,copy=True)
    car_percent = fields.Float('CAR Percent',copy=True)
    financial_cost = fields.Float('Financial Cost During Construction',copy=True)
    financial_cost_percent = fields.Float('Financial Cost Percent',compute="_compute_fin_cost_percent",store=True,copy=True)
    bank_guarantee = fields.Float('Bank Guarantee',copy=True)
    bank_guarantee_percent = fields.Float('Bank Guarantee percent',compute="_compute_bank_guarantee_percent",store=True,copy=True)
    contigency = fields.Float('Contigency',compute="_compute_contigency",store=True,copy=True)
    contigency_percent = fields.Float('Contigency Percent',copy=True)
    waranty = fields.Float('Waranty',compute="_compute_waranty",store=True,copy=True)
    waranty_percent = fields.Float('Waranty Percent',copy=True)
    
    
    currency_id = fields.Many2one('res.currency', string='currency',default=lambda self:self.env.company.currency_id.id)
    project_value = fields.Float(compute='_compute_project_value', string='Project Value',store=True)
    profit = fields.Float('Profit',compute="_compute_profit",store=True)
    sales = fields.Float('Sales',compute="_compute_profit",store=True)
    profit_percent = fields.Float('Profit Proportional %')
    offer_margin_percent = fields.Float('Offer Margin Percent')
    offer_margin = fields.Float('Offer Margin',compute="_compute_offer_margin",store=True)
    total_cost_with_margin = fields.Float('Total Cost + Offer Margin',compute="_compute_total_amount",store=True)
    total_cost_round_up = fields.Float('Round Up',compute="_compute_total_amount",store=True)
    final_profit = fields.Float('Final Profit',compute="_compute_total_amount",store=True)
    final_profit_percent = fields.Float('Final Profit Proportional %',compute="_compute_total_amount",store=True)
    taxes = fields.Float('Taxes',compute="_compute_total_amount",store=True)
    total_amount = fields.Float(compute='_compute_total_amount', string='Total Amount',store=True)
    
    def create_revision(self):
        
        new_name = self.name[0: self.name.index(' Rev.')] if self.revisied else self.name
        data = self.copy({
            'name': "%s Rev. %s"%(new_name,self.rev + 1),
            'rev': self.rev + 1,
            'cost_sheet_revision_id' : self.id,
            'revisied': True
        })
        
        
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "cost.sheet",
            "res_id": data.id
        }
        
    
    
    @api.depends('rab_line_ids','ga_project','project_hse','car','financial_cost','bank_guarantee','contigency','waranty')
    def _compute_project_value(self):
        for this in self:
            amount_project = sum(this.rab_line_ids.mapped('price_unit'))
            amount_non_project = sum([this.ga_project,this.project_hse,this.car,this.financial_cost,this.bank_guarantee,this.contigency,this.waranty])
            this.project_value = amount_project + amount_non_project
            
    
    
    @api.depends('ga_project_line_ids.total_price','project_value')
    def _compute_ga_project(self):
        for this in self:
            this.ga_project = sum(this.ga_project_line_ids.mapped('total_price'))
            this.ga_project_percent = sum(this.ga_project_line_ids.mapped('total_price')) / this.project_value if this.ga_project_line_ids and this.project_value > 0 else 0.0
            
    @api.depends('ga_project','project_hse_percent')
    def _compute_project_hse(self):
        for this in self:
            this.project_hse = this.ga_project * this.project_hse_percent
    @api.depends('rab_line_ids.price_unit','car_percent')
    def _compute_car(self):
        for this in self:
            this.car = sum(this.rab_line_ids.mapped('price_unit')) * this.car_percent
            
    @api.depends('project_value','financial_cost')
    def _compute_fin_cost_percent(self):
        for this in self:
            this.financial_cost_percent = this.financial_cost / this.project_value if this.financial_cost >0 and this.project_value > 0 else 0.0
    @api.depends('project_value','bank_guarantee')
    def _compute_bank_guarantee_percent(self):
        for this in self:
            this.bank_guarantee_percent = this.bank_guarantee / this.project_value if this.bank_guarantee >0 and this.project_value > 0 else 0.0

    @api.depends('rab_line_ids.price_unit','contigency_percent')
    def _compute_contigency(self):
        for this in self:
            this.contigency = sum(this.rab_line_ids.mapped('price_unit')) * this.contigency_percent
            
    @api.depends('rab_line_ids.price_unit','waranty_percent')
    def _compute_waranty(self):
        for this in self:
            this.waranty = sum(this.rab_line_ids.mapped('price_unit')) * this.waranty_percent
            
            
    @api.depends('project_value','profit_percent')
    def _compute_profit(self):
        for this in self:
            profit = 0.0
            sales = 0.0
            sales = this.project_value / (1 - this.profit_percent)
            profit = sales - this.project_value
            this.sales = sales
            this.profit = profit
    
    @api.depends('offer_margin_percent','sales')
    def _compute_offer_margin(self):
        for this in self:
            this.offer_margin = this.offer_margin_percent * this.sales
            
            
    @api.depends('offer_margin_percent','offer_margin','sales','project_value','tax_id')
    def _compute_total_amount(self):
        for this in self:
            total_cost = 0.0
            round_up = 0.0
            final_profit = 0.0
            final_profit_percent = 0.0
            taxes = 0.0
            total_amount = 0.0
            
            total_cost = this.offer_margin + this.sales
            round_up = float_round(total_cost,precision_digits=-6,rounding_method='UP') if total_cost > 0 else 0.0
            final_profit = round_up - this.project_value
            final_profit_percent = final_profit/round_up if this.project_value >0 and round_up >0 else 0.0
            taxes = round_up * (this.tax_id.amount/100)
            total_amount = round_up + taxes
            
            
            this.total_cost_with_margin = total_cost
            this.total_cost_round_up = round_up
            this.final_profit = final_profit
            this.final_profit_percent = final_profit_percent
            this.taxes = taxes
            this.total_amount = total_amount
    
    # TOTAL PER LINE
    # total_rab_line = fields.Float(compute='_compute_total',store=True)
    # total_general_work = fields.Float(compute='_compute_total',store=True)
    # total_intake_package = fields.Float(compute='_compute_total',store=True)
    # total_pretreatment_package = fields.Float(compute='_compute_total',store=True)
    # swro_package_total = fields.Float(compute='_compute_total',store=True)
    # total_brine_injection_package = fields.Float(compute='_compute_total',store=True)
    # total_product_package = fields.Float(compute='_compute_total',store=True)
    # total_electrical_package = fields.Float(compute='_compute_total',store=True)
    # total_civil_work = fields.Float(compute='_compute_total',store=True)
    # total_ga_project = fields.Float(compute='_compute_total',store=True)
    # total_waranty = fields.Float(compute='_compute_total',store=True)
    
    # a = float_round(3044686682.41547,precision_digits=-6,rounding_method='UP')
    # 
    # @api.depends(
    #     'rab_line_ids',
    #     'general_work_line_ids',
    #     'intake_package_line_ids',
    #     'pretreatment_package_line_ids',
    #     'swro_package_line_ids',
    #     'brine_injection_package_line_ids',
    #     'product_package_line_ids',
    #     'electrical_package_line_ids',
    #     'civil_work_line_ids',
    #     'ga_project_line_ids',
    #     'waranty_line_ids',
    #     )
    # def _compute_total(self):
    #     for this in self:
    #         this.total_rab_line = sum(this.mapped('rab_line_ids.price_unit'))
    #         this.total_general_work = sum(this.mapped('general_work_line_ids.total_price'))
    #         this.total_intake_package = sum(this.mapped('intake_package_line_ids.total_price'))
    #         this.total_pretreatment_package = sum(this.mapped('pretreatment_package_line_ids.total_price'))
    #         this.swro_package_total = sum(this.mapped('swro_package_line_ids.total_price'))
    #         this.total_brine_injection_package = sum(this.mapped('brine_injection_package_line_ids.total_price'))
    #         this.total_product_package = sum(this.mapped('product_package_line_ids.total_price'))
    #         this.total_electrical_package = sum(this.mapped('electrical_package_line_ids.total_price'))
    #         this.total_civil_work = sum(this.mapped('civil_work_line_ids.total_price'))
    #         this.total_ga_project = sum(this.mapped('ga_project_line_ids.total_price'))
    #         this.total_waranty = sum(this.mapped('waranty_line_ids.total_price'))
    
    
    
    def action_create_requisition(self):
        request = self.env['purchase.requisition'].create({
            'user_id': self.env.uid,
            'ordering_date': fields.Date.today(),
            'origin': self.name,
            'line_ids':[(0,0,{
                'product_id':data.product_id.id,
                'product_description_variants': data.product_id.name,
                'product_qty': data.product_qty,
                'price_unit': data.price_unit
            })for data in self.line_ids if not data.display_type]
        })
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "purchase.requisition",
            "res_id": request.id
        }
    
    
    # @api.onchange('margin_type')
    # def _onchange_margin_type(self):
    #     self.margin_amount_input = 0.0
    #     self.margin_percent_input = 0.0
    
    # @api.onchange('margin_percent_input')
    # def _onchange_margin_percent_input(self):
    #     if self.margin_percent_input:
    #         self.line_ids.write({'margin_percent':self.margin_percent_input})
    #     else:
    #         self.line_ids.write({'margin_percent':self.margin_percent_input})
            
    
    @api.onchange('crm_id')
    def _onchange_crm_id(self):
        if self.crm_id and self.crm_id.partner_id:
            self.partner_id = self.crm_id.partner_id.id
   
    def action_submit(self):
        self.write({'state':'submit'})
    def action_done(self):
        self.write({'state':'done'})
    def action_to_draft(self):
        self.write({'state':'draft'})
    
 
    def action_view_crm(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "crm.lead",
            "res_id": self.crm_id.id
        }
        
    def action_print_rab(self):
        return self.env.ref('solinda_cost_sheet.action_report_cost_sheet').report_action(self)

    @api.model
    def create(self, vals):
        res = super(CostSheet, self).create(vals)
        if "Rev. " not in res.name:
            res.name = self.env["ir.sequence"].next_by_code("cost.sheet.seq")
        else:
            return res
        res.crm_id.rab_id = res.id
        return res 
    
   
    @api.onchange('rab_template_id')
    def _onchange_rab_template_id(self):
        if self.line_ids:
            self.write({
                'line_ids': [(5,0,0)]
            })
        else:        
            self.write({
                'line_ids': [(0,0,{
                    'name': template.name,
                    'display_type': template.display_type,
                    'sequence': template.sequence,
                    'product_id': template.product_id.id,
                    'product_qty': template.product_qty,
                    'uom_id': template.uom_id.id,
                    'vol_factor': template.vol_factor,
                    'item_factor': template.item_factor,
                    'lab_factor': template.lab_factor,
                    'start_date': template.start_date,
                    'end_date': template.end_date,
                    'no_pos': template.no_pos,
                    'price_unit': template.price_unit,
                    'margin_percent': template.margin_percent
                }) for template in self.rab_template_id.line_ids]
        }) 

# RAB 

class RabLine(models.Model):
    _name = 'rab.line'
    _description = 'Rab Line'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Text('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    price_unit = fields.Float(compute='_compute_amount', string='Price',store=True)
    propotional_percent = fields.Float(compute='_compute_amount_propotional', string='Propotional %',store=False)
    suggested_proposional_percent = fields.Float(compute='_compute_amount', string='Sug. Commercial Price',store=True)
    input_manual = fields.Boolean('Adjust Manual')
    commercial_price  = fields.Float('Final Price',compute="_compute_final_price",inverse="_inverse_final_price")
    commercial_price_percentage = fields.Float('Final %')
    
    # total_amount = fields.Float('Total Amount',compute="_compute_final_price",store=True)
       
    
    @api.depends('cost_sheet_id.total_cost_round_up','input_manual','price_unit','commercial_price_percentage')
    def _compute_final_price(self):
        for this in self:
            amount = 0.0
            total_amount = 0.0
            total_input_amount = 0.0
            if this.cost_sheet_id.total_cost_round_up > 0 :
                # while this.commercial_price == this.cost_sheet_id.total_cost_round_up:
                if this.input_manual:
                    percent = sum(this.cost_sheet_id.rab_line_ids.mapped('commercial_price_percentage')) - this.commercial_price_percentage
                    diff_percent = 1 - percent if percent < 1 else percent-1
                    print("====================== PERCENT",percent)
                    print("====================== DIFFF PERCENT",diff_percent)
                    # this.commercial_price = 0.0
                    # this.commercial_price_percentage = 0.0
                    # total_input_amount = this.cost_sheet_id.total_cost_round_up - sum(this.cost_sheet_id.rab_line_ids.mapped('commercial_price')) - this.commercial_price
                    this.commercial_price =  this.cost_sheet_id.total_cost_round_up * diff_percent
                    this.write({'commercial_price_percentage': diff_percent})
                # this.commercial_price_percentage = total_input_amount/ this.cost_sheet_id.total_cost_rou
                    # this.commercial_price = 0.0
                    # this.commercial_price_percentage = 0.0
                    # total_input_amount = this.cost_sheet_id.total_cost_round_up - sum(this.cost_sheet_id.rab_line_ids.mapped('commercial_price')) - this.commercial_price
                    # this.commercial_price =  total_input_amount
                    # this.commercial_price_percentage = total_input_amount/ this.cost_sheet_id.total_cost_round_up
                else:
                    amount = this.commercial_price_percentage * this.cost_sheet_id.total_cost_round_up
                    total_amount = float_round(amount,precision_digits=-5,rounding_method='UP')
                    this.commercial_price =  total_amount
                    
            else:
                this.commercial_price = 0.0
                this.commercial_price_percentage = 0.0
                
    
    def _inverse_final_price(self):
        for this in self:
            amount = 0.0
            total_amount = 0.0
            total_input_amount = 0.0
            if this.input_manual:
                percent = sum(this.cost_sheet_id.rab_line_ids.mapped('commercial_price_percentage')) - this.commercial_price_percentage
                diff_percent = 1 - percent if percent < 1 else percent-1
                print("====================== PERCENT",percent)
                print("====================== DIFFF PERCENT",diff_percent)
                # this.commercial_price = 0.0
                # this.commercial_price_percentage = 0.0
                # total_input_amount = this.cost_sheet_id.total_cost_round_up - sum(this.cost_sheet_id.rab_line_ids.mapped('commercial_price')) - this.commercial_price
                this.commercial_price =  this.cost_sheet_id.total_cost_round_up * diff_percent
                # this.commercial_price_percentage = diff_percent
                this.write({'commercial_price_percentage': diff_percent})

                # this.commercial_price_percentage = total_input_amount/ this.cost_sheet_id.total_cost_round_up
            else:
                # continue
                amount = this.commercial_price_percentage * this.cost_sheet_id.total_cost_round_up
                total_amount = float_round(amount,precision_digits=-5,rounding_method='UP')
                this.commercial_price =  total_amount
                
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
    
    @api.depends(
            'product_id',
            'cost_sheet_id.intake_package_line_ids.product_qty',
            'cost_sheet_id.intake_package_line_ids.rfq_price',
            'cost_sheet_id.general_work_line_ids.product_qty',
            'cost_sheet_id.general_work_line_ids.rfq_price',
            'cost_sheet_id.pretreatment_package_line_ids.product_qty',
            'cost_sheet_id.pretreatment_package_line_ids.rfq_price',
            'cost_sheet_id.swro_package_line_ids.product_qty',
            'cost_sheet_id.swro_package_line_ids.rfq_price',
            'cost_sheet_id.brine_injection_package_line_ids.product_qty',
            'cost_sheet_id.brine_injection_package_line_ids.rfq_price',
            'cost_sheet_id.product_package_line_ids.product_qty',
            'cost_sheet_id.product_package_line_ids.rfq_price',
            'cost_sheet_id.electrical_package_line_ids.product_qty',
            'cost_sheet_id.electrical_package_line_ids.rfq_price',
            'cost_sheet_id.civil_work_line_ids.product_qty',
            'cost_sheet_id.civil_work_line_ids.rfq_price',
            'cost_sheet_id.ga_project_line_ids',
            'cost_sheet_id.waranty_line_ids',
            
            
        )
    def _compute_amount(self):
        for this in self:
            amount = 0
            pro_percent = 0
            sugg_pro_percent = 0
            
            if this.product_id.product_group == 'general_work':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.general_work_line_ids])
            elif this.product_id.product_group == 'intake_package':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.intake_package_line_ids])
            elif this.product_id.product_group == 'pretreatment_package':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.pretreatment_package_line_ids])
            elif this.product_id.product_group == 'swro_package':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.swro_package_line_ids])
            elif this.product_id.product_group == 'brine_injection_package':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.brine_injection_package_line_ids])
            elif this.product_id.product_group == 'product_package':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.product_package_line_ids])
            elif this.product_id.product_group == 'electrical_package':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.electrical_package_line_ids])
            elif this.product_id.product_group == 'civil_work':
                amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.civil_work_line_ids])
            # elif this.product_id.product_group == 'ga_project':
            #     amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.ga_project_line_ids])
            # elif this.product_id.product_group == 'waranty':
            #     amount = sum([(i.product_qty * i.rfq_price) for i in this.cost_sheet_id.waranty_line_ids])
                
            this.price_unit = amount
            this.suggested_proposional_percent = sugg_pro_percent
    
    # @api.depends('price_unit','product_id')
    def _compute_amount_propotional(self):
        for this in self:
            pro_percent = 0.0
            pro_percent = this.price_unit / sum([(i.price_unit) for i in this.cost_sheet_id.rab_line_ids]) if this.price_unit > 0 else 0.0
            this.propotional_percent = pro_percent
            
             
    
    @api.model
    def create(self, vals):
        res = super(RabLine, self).create(vals)
        data = []
        if res.product_id.product_group == 'general_work':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'type': 'general_work',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })            
                res.cost_sheet_id.general_work_line_ids.create(data)
        elif res.product_id.product_group == 'intake_package':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.intake_package_line_ids.create(data)         
        elif res.product_id.product_group == 'pretreatment_package':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.pretreatment_package_line_ids.create(data)         
        elif res.product_id.product_group == 'swro_package':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.swro_package_line_ids.create(data)         
        elif res.product_id.product_group == 'brine_injection_package':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.brine_injection_package_line_ids.create(data)         
        elif res.product_id.product_group == 'product_package':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.product_package_line_ids.create(data)         
        elif res.product_id.product_group == 'electrical_package':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.electrical_package_line_ids.create(data)         
        elif res.product_id.product_group == 'civil_work':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.civil_work_line_ids.create(data)         
        elif res.product_id.product_group == 'ga_project':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.ga_project_line_ids.create(data)         
        elif res.product_id.product_group == 'waranty':
            if res.product_id.bom_ids:
                data.append({
                'cost_sheet_id': res.cost_sheet_id.id,
                'name': res.product_id.name,
                'display_type': 'line_section',
                'rab_line_id': res.id
                })
                for bom in res.product_id.bom_ids[0].rab_component_line_ids:
                    data.append({
                        'cost_sheet_id': res.cost_sheet_id.id,
                        'display_type': False,
                        'product_id': bom.product_id.id,
                        'name': bom.product_id.display_name,
                        'product_qty': bom.product_qty,
                        'uom_id' : bom.product_uom_id.id,
                        'existing_price': bom.product_id.list_price,
                        'rfq_price' : bom.product_id.list_price,
                        'rab_line_id': res.id
                    })   
                res.cost_sheet_id.waranty_line_ids.create(data)         
        return res 
    
    
class GeneralWork(models.Model):
    _name = 'general.work'
    _description = 'General Work'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
        
    
class IntakePackage(models.Model):
    _name = 'intake.package'
    _description = 'Intake Package'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
        
class PretreatmentPackage(models.Model):
    _name = 'pretreatment.package'
    _description = 'Pretreatment Package'
    
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
        
    
class SwroPackage(models.Model):
    _name = 'swro.package'
    _description = 'Swro Package'
    
    
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
        
    
class BrineInjectionPackage(models.Model):
    _name = 'brine.injection.package'
    _description = 'Brine Injection Package'
    
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
        
class ProductPackage(models.Model):
    _name = 'product.package'
    _description = 'Product Package'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
        
    
class ElectricalPackage(models.Model):
    _name = 'electrical.package'
    _description = 'Electrical Package'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
    
class CivilWork(models.Model):
    _name = 'civil.work'
    _description = 'Civil Work'
    
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
    
    
class GaProject(models.Model):
    _name = 'ga.project'
    _description = 'GA Project'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
    
    
class WarantyWaranty(models.Model):
    _name = 'waranty.waranty'
    _description = 'Waranty Waranty'
    
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', related='cost_sheet_id.partner_id', string='Partner', readonly=True, store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    name = fields.Char('Description')
    note = fields.Char('Remarks')
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    rab_line_id = fields.Many2one('rab.line', string='RAB Line',ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.env.company.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name
        
        self.rfq_price = self.product_id.list_price
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            total = 0.0
            total = this.product_qty * this.rfq_price
            this.total_price = total
    
    



class ProjectRab(models.Model):
    _name = 'project.rab'
    _description = 'Project RAB'

    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    rab_template_id = fields.Many2one('rab.template', string='RAB Template')
    # project_id = fields.Many2one('project.project', string='Project')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')

    product_id = fields.Many2one('product.product', string='Product')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    name = fields.Char('Description')
    
    product_qty = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    vol_factor = fields.Float('Volume Factor')
    item_factor = fields.Float('Item Factor')
    lab_factor = fields.Float('Lab Factor')
    price_unit = fields.Float('Price')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('Finish Date')
    no_pos = fields.Char('No')
    margin = fields.Float('Margin',compute='_compute_price')
    margin_percent = fields.Float(string='Margin Percent',compute='_compute_price')
    price_subtotal = fields.Float(compute='_compute_price', string='Subtotal')
    
    price_final = fields.Float('Price Final')    
    
    def create_requisition(self):
        request = self.env['purchase.requisition'].create({
            'user_id': self.env.uid,
            'ordering_date': fields.Date.today(),
            'origin': self.cost_sheet_id.name,
            'line_ids':[(0,0,{
                'product_id':self.product_id.id,
                'product_qty': self.product_qty,
                'price_unit': self.price_unit
            })]
        })
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "purchase.requisition",
            "res_id": request.id
        }


    
    # @api.depends('price_unit','cost_sheet_id.margin_percent_input','cost_sheet_id.margin_amount_input')
    def _compute_price(self):
        for this in self:
            margin = 0.0
            margin_percent = 0.0
            subtotal = 0.0
            if this.cost_sheet_id.margin_type == 'percentage':
                margin_percent = this.cost_sheet_id.margin_percent_input
                margin = this.price_unit * margin_percent
                subtotal = this.price_unit * this.product_qty + margin
            else:
                margin_percent = 0.0
                margin = 0.0
                subtotal = this.price_unit * this.product_qty 
               
                
            this.margin = margin
            this.margin_percent = margin_percent
            this.price_subtotal = subtotal
            


class RabTemplate(models.Model):
    _name = 'rab.template'
    _description = 'RAB Template'

    name = fields.Char('Name of Template')
    line_ids = fields.One2many('project.rab', 'rab_template_id', string='Rab Line')

    
